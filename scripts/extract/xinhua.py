from typing import List

from common import Cookie, CookieJar
from loguru import logger
from pydantic import Field

from .crawler import Crawler


class XinhuaCrawler(Crawler):
    base_url: str = Field(
        default="https://github.com/pwxcoo/chinese-xinhua/raw/master/data/{key}.json"
    )

    def format_url(self, jar: CookieJar) -> str:
        match jar.extractor.split("."):
            case "crawler", "xinhua", key:
                return self.base_url.format(key=key)
            case _:
                raise ValueError(f"XinhuaCrawler: Invalid extractor: {jar.extractor}")

    def parse_xiehouyu(self, data: dict) -> Cookie:
        return Cookie(
            content=f"{data.get('riddle')} -- {data.get('answer')}",
        )

    def parse_ci(self, data: dict) -> Cookie:
        return Cookie(
            content=f"「{data.get('ci')}」\n{data.get('explanation')}",
        )

    def parse_idiom(self, data: dict) -> Cookie:
        return Cookie(
            content=f"「{data.get('word')}」\n拼音: ({data.get('pinyin')})\n出处: {data.get('derivation')}\n释义: {data.get('explanation')}",
        )

    def get_popular_idioms(self) -> List[str]:
        link = "https://github.com/thunlp/THUOCL/raw/refs/heads/master/data/THUOCL_chengyu.txt"
        # 首先获取清华成语库，因为此词库包括词频，因此可以优选高频成语
        thuolc_idioms_text = self.get_raw_text(link)
        thuolc_idioms = []
        for line in thuolc_idioms_text.split("\n"):
            line = line.strip()
            if line and "\t" in line:
                parts = line.split("\t")
                thuolc_idioms.append(
                    {"word": parts[0].strip(), "count": int(parts[1].strip())}
                )
        # 按词频排序，取前1000个
        thuolc_idioms = sorted(thuolc_idioms, key=lambda x: x["count"], reverse=True)
        popular_idioms = [x["word"] for x in thuolc_idioms[:1500]]
        return popular_idioms

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")

        _, _, key = jar.extractor.split(".")

        if key == "idiom":
            popular_idioms = self.get_popular_idioms()

        cookies = []
        jar.link = self.base_url.format(key=key)
        data = self.get_json(jar.link)
        if not data:
            return cookies

        for item in data:
            match key:
                case "xiehouyu":
                    cookie = self.parse_xiehouyu(item)
                case "ci":
                    cookie = self.parse_ci(item)
                case "idiom":
                    if item.get("word") in popular_idioms:
                        cookie = self.parse_idiom(item)
                    else:
                        continue
                case _:
                    raise ValueError(f"Invalid extractor: {jar.extractor}")
            cookie.source = f"《{jar.name}》"
            cookie.link = jar.link
            cookies.append(cookie)

        logger.info(f"爬取 《{jar.name}》 完成, 共爬取 {len(cookies)} 条。")
        return cookies

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        parts = jar.extractor.split(".")
        match parts[1]:
            case "xinhua":
                crawler = XinhuaCrawler()
                return crawler.crawl(jar)
            case _:
                raise ValueError(f"XinhuaCrawler: Invalid extractor: {jar.extractor}")
