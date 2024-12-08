import random
import time
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger
from model import Cookie, CookieJar
from pydantic import BaseModel, Field
from requests_cache import CachedSession

# 设置缓存，有效期为1个月
# requests_cache.install_cache(
#     "data/cache/crawler.db", backend="sqlite", expire_after=86400 * 30
# )

session = CachedSession(
    "data/cache/crawler.db", backend="sqlite", expire_after=86400 * 30
)


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

    def get_page(self, url) -> BeautifulSoup:
        """获取页面内容并返回 BeautifulSoup 对象"""
        try:
            # 对于已经缓存的请求，不再延迟；对于新请求，随机延迟一段时间
            # if not requests_cache.get_cache().contains(url=url):
            if not session.cache.contains(url=url):
                time.sleep(random.uniform(self.interval / 3, self.interval))
            # response = requests.get(url, headers=self.headers)
            response = session.get(url, headers=self.headers)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            self.remove_link_from_cache(url)
            return None

    def get_text(self, element) -> str:
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

    def remove_link_from_cache(self, url):
        logger.debug(f"Removing {url} from crawler cache")
        session.cache.delete(urls=[url])

    def parse_item(self, element) -> Cookie:
        raise NotImplementedError

    def parse_list(self, element) -> List:
        raise NotImplementedError

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        raise NotImplementedError

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", "gushiwen", _, _:
                from .gushiwen import GushiwenCrawler

                return GushiwenCrawler.extract(jar)
            case _:
                raise NotImplementedError
