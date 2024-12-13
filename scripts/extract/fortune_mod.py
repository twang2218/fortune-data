from typing import List

from common import Cookie, CookieJar
from loguru import logger
from pydantic import Field

from .crawler import Crawler


class ForturnModCrawler(Crawler):
    base_url: str = Field(
        default="https://github.com/shlomif/fortune-mod/raw/refs/heads/master/fortune-mod/datfiles/{key}"
    )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")

        _, _, key = jar.extractor.split(".")
        url = self.base_url.format(key=key)
        data = self.get_raw_text(url)
        cookies = []
        for quote in data.split("\n%\n"):
            quote = quote.rstrip("%").strip()
            if quote and not quote.startswith("#"):
                # split content and source from the quote
                parts = quote.split("\t\t--")
                if len(parts) == 2:
                    content, source = parts
                    cookies.append(
                        Cookie(
                            content=content.strip(),
                            source=source.strip(),
                            link=jar.link,
                        )
                    )
                else:
                    cookies.append(Cookie(content=quote, link=jar.link))
        logger.info(f"爬取完成 《{jar.name}》: {len(cookies)} 条")
        return cookies

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        parts = jar.extractor.split(".")
        match parts[0], parts[1]:
            case "crawler", "fortune_mod":
                return ForturnModCrawler().crawl(jar)
            case _:
                raise ValueError(
                    f"ForturnModCrawler: Invalid extractor: {jar.extractor}"
                )
