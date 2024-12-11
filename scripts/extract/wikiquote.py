import re
from typing import List, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from common import Agent, Cookie, CookieJar

from .crawler import Crawler


class Quote(BaseModel):
    quote: str = Field(
        default="", description="The quote text extracted from the content."
    )
    source: str = Field(
        default="", description="The source of the quote extracted from the content."
    )


class WikiQuoteCrawler(Crawler):
    base_url: str = Field(default="https://{lang}.wikiquote.org/wiki/{title}")
    whitelist: List[str] = Field(
        default=[],
        description="whitelist, only crawl the title in the white list",
    )
    blacklist: List[str] = Field(
        default=[],
        description="blacklist, never crawl the title in the black list",
    )
    prompt: str = Field(
        default="Please evaluate the following content, and extract the quote and source(if applicable) from the given text only. Do not add, infer, or supplement any information that is not explicitly present in the given text. Do not include any additional commentary or background information that follows.",
    )
    source_leadings: List[str] = Field(
        default=["--"],
        description="The leading characters to remove from the source text.",
    )
    parentheses_left: List[str] = Field(
        default=["\\[", "\\("],
        description="The left parentheses to remove from the source text.",
    )
    parentheses_right: List[str] = Field(
        default=["\\]", "\\)"],
        description="The right parentheses to remove from the source text.",
    )

    def format_url(self, jar: CookieJar) -> str:
        _, _, lang = jar.extractor.split(".")
        return self.base_url.format(title=jar.name, lang=lang)

    def parse_list(self, soup) -> List[str]:
        quotes = []
        body = soup.select_one("div.mw-parser-output")
        current_title = ""
        for item in body.select("div.mw-heading2 h2, div.mw-parser-output > ul > li"):
            if item.name == "h2":
                current_title = item.text
            if item.name == "li":
                # if current_title in self.whitelist:
                if current_title not in self.blacklist:
                    quotes.append(item)
        return quotes

    def parse_element_text(self, element) -> str:
        text = ""
        for content in element.contents:
            if isinstance(content, str):
                text += content.strip()
            elif content.name == "a":
                text += content.text.strip()
            elif content.name == "br":
                text += "\n"
            elif content.name == "b":
                text += content.text.strip()
            elif content.name == "i":
                text += content.text.strip()
            elif content.name == "strong":
                text += content.text.strip()
            elif content.name in ["sup", "span"]:
                continue
            else:
                continue
        return text

    def parse_item(self, element) -> Cookie:
        # 提取名言部分
        source_element = element.find("dd")
        if not source_element:
            source_element = element.find("li")
        if not source_element:
            adjacent = element.next_sibling
            if not adjacent:
                adjacent = element.parent.next_sibling if element.parent else None
            if adjacent:
                if adjacent.name == "dl":
                    source_element = adjacent.find("dd")
                elif adjacent.name == "p" and len(adjacent.text.strip()) < 50:
                    source_element = adjacent

        content = self.parse_element_text(element)
        source = self.parse_source(source_element)

        if not source:
            # 尝试从 content 中提取 source
            content, source = self.parse_source_from_content(content)

        return Cookie(
            content=content,
            source=source,
        )

    def parse_source(self, element) -> str:
        source = self.parse_element_text(element) if element else ""
        if source:
            for leading in self.source_leadings:
                source = source.strip().lstrip(leading).strip()
        return source

    def parse_source_from_content(self, content: str) -> Tuple[str, str]:
        left = "".join([f"{p}" for p in self.parentheses_left])
        right = "".join([f"{p}" for p in self.parentheses_right])
        pattern = re.compile(r"^(.*?)(?:[" + left + r"](.*?)[" + right + r"])\s*$")
        m = pattern.match(content)
        if m:
            quote = m.group(1).strip()
            source = m.group(2).strip()
            return quote, source
        else:
            return content, ""

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []
        jar.link = self.format_url(jar)
        soup = self.get_page(jar.link)
        if not soup:
            return cookies

        for item in self.parse_list(soup):
            cookie = self.parse_item(item)
            if cookie.content:
                cookie.link = jar.link
                cookies.append(cookie)

        cookies = self.process_cookies(cookies, jar)

        logger.info(f"爬取 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies

    def process_content_by_llm(
        self, cookies: List[Cookie], jar: CookieJar
    ) -> List[Cookie]:
        agent = Agent(prompt=self.prompt, base_model=jar.model_name, cls=Quote)
        cookies_with_source = [cookie for cookie in cookies if cookie.source]
        cookies_without_source = [cookie for cookie in cookies if not cookie.source]
        quotes = agent.process([cookie.content for cookie in cookies_without_source])
        for i, quote in enumerate(quotes):
            cookie = cookies_without_source[i]
            if isinstance(quote, Quote):
                cookie.content = quote.quote.strip()
                cookie.source = quote.source.strip()
            else:
                cookie.source = jar.name
            cookies_with_source.append(cookie)
        return cookies_with_source

    def process_source(self, cookies: List[Cookie], jar: CookieJar) -> List[Cookie]:
        for cookie in cookies:
            if jar.name not in cookie.source:
                cookie.source = f"{cookie.source} {jar.name}"
                cookie.source = cookie.source.strip()

            if not cookie.source:
                cookie.source = jar.name

        return cookies

    def process_cookies(self, cookies: List[Cookie], jar: CookieJar) -> List[Cookie]:
        cookies = self.process_content_by_llm(cookies, jar)
        cookies = self.process_source(cookies, jar)
        return cookies

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", "wikiquote", "zh":
                crawler = ZhWikiQuoteCrawler()
                return crawler.crawl(jar)
            case "crawler", "wikiquote", "en":
                crawler = EnWikiQuoteCrawler()
                return crawler.crawl(jar)
            case "crawler", "wikiquote", _:
                crawler = WikiQuoteCrawler()
                return crawler.crawl
            case _:
                raise ValueError(
                    f"WikiQuoteCrawler: Invalid extractor: {jar.extractor}"
                )


class EnWikiQuoteCrawler(WikiQuoteCrawler):
    def format_url(self, jar: CookieJar) -> str:
        return self.base_url.format(title=jar.name, lang="en")


class ZhWikiQuoteCrawler(WikiQuoteCrawler):
    whitelist: List[str] = Field(
        default=["语录", "語錄", "名言", "作品摘录"],
        description="白名单，只爬取白名单内的标题",
    )
    blacklist: List[str] = Field(
        default=["模板", "分类", "帮助", "MediaWiki", "Wikiquote", "参见", "参考文献"],
        description="黑名单，不爬取黑名单内的标题",
    )
    source_leadings: List[str] = Field(
        default=["--", "——", "出自", "引自", "来源", "摘自"],
        description="需要移除的引用前缀",
    )
    parentheses_left: List[str] = Field(
        default=["\\[", "\\(", "（", "【", "《"],
        description="The left parentheses to remove from the source text.",
    )
    parentheses_right: List[str] = Field(
        default=["\\]", "\\)", "）", "】", "》"],
        description="The right parentheses to remove from the source text.",
    )

    def format_url(self, jar: CookieJar) -> str:
        return self.base_url.format(title=jar.name, lang="zh")

    def process_source(self, cookies: List[Cookie], jar: CookieJar) -> List[Cookie]:
        for cookie in cookies:
            if cookie.source and "《" not in cookie.source:
                cookie.source = f"《{cookie.source}》"

        cookies = super().process_source(cookies, jar)

        return cookies
