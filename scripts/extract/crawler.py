import random
import time
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from common import Cookie, CookieJar
from loguru import logger
from pydantic import BaseModel, Field
from requests_cache import AnyResponse, CachedSession

session = None


class Crawler(BaseModel):
    base_url: str = Field(default="", description="The base URL of the website.")
    max_page: int = Field(
        default=100, description="The maximum number of pages to crawl."
    )
    interval: float = Field(
        default=1, description="The interval between requests in seconds."
    )
    headers: dict = Field(
        default={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        },
        description="The headers to be used in requests.",
    )

    def get_response(self, url) -> AnyResponse:
        """获取页面 Response 对象"""
        global session
        try:
            # 对于已经缓存的请求，不再延迟；对于新请求，随机延迟一段时间
            if not session.cache.contains(url=url):
                time.sleep(random.uniform(self.interval / 3, self.interval))
            response = session.get(url, headers=self.headers)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response
        except Exception as e:
            logger.error(f"Crawler.get_response(): Error fetching {url}: {str(e)}")
            self.remove_link_from_cache(url)
            return None

    def get_page(self, url) -> BeautifulSoup:
        """获取页面内容并返回 BeautifulSoup 对象"""
        resp = self.get_response(url)
        if not resp:
            return None
        return BeautifulSoup(resp.text, "html5lib")

    def get_json(self, url) -> dict:
        """获取 JSON 数据"""
        resp = self.get_response(url)
        if not resp:
            return None
        return resp.json()

    def get_raw_text(self, url) -> str:
        """获取页面内容并返回文本"""
        resp = self.get_response(url)
        if not resp:
            return None
        return resp.text

    def get_content(self, element) -> str:
        """获取文本内容"""
        if not element:
            return None
        # 保留换行信息
        for br in element.find_all("br"):
            br.replace_with("\n")
        for p in element.find_all("p"):
            p.replace_with("\n" + p.text)
        return element.text.strip()

    def get_link(self, link) -> str:
        if link and link.has_attr("href"):
            return urljoin(self.base_url, link["href"])
        return None

    def parse_item(self, element) -> Cookie:
        raise NotImplementedError

    def parse_list(self, element) -> List:
        raise NotImplementedError

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        raise NotImplementedError

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        parts = jar.extractor.split(".")
        match parts[0], parts[1]:
            case "crawler", "gushiwen":
                from .gushiwen import GushiwenCrawler

                return GushiwenCrawler.extract(jar)
            case "crawler", "xinhua":
                from .xinhua import XinhuaCrawler

                return XinhuaCrawler.extract(jar)
            case "crawler", "wikiquote":
                from .wikiquote import WikiQuoteCrawler

                return WikiQuoteCrawler.extract(jar)
            case "crawler", "fortune_mod":
                from .fortune_mod import ForturnModCrawler

                return ForturnModCrawler.extract(jar)
            case _:
                raise NotImplementedError

    @staticmethod
    def init_cache(cache_dir: str = None):
        global session
        if not cache_dir:
            cache_dir = str(Path(__file__).parent.parent / ".cache" / "crawler.db")
        else:
            cache_dir = str(Path(cache_dir) / "crawler.db")
        logger.debug(f"Crawler cache: {cache_dir}")
        session = CachedSession(cache_dir, backend="sqlite", expire_after=86400 * 30)

    @staticmethod
    def remove_link_from_cache(url):
        global session
        if not session:
            return
        logger.debug(f"Removing {url} from crawler cache")
        session.cache.delete(urls=[url])

    @staticmethod
    def exists_in_cache(url):
        global session
        if not session:
            return False
        return session.cache.contains(url=url)
