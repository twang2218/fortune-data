from typing import Any, List

from loguru import logger
from model import Cookie, CookieJar
from pydantic import BaseModel, Field
from utils import get_llm_chain, remove_from_cache

from .crawler import Crawler


class WikiQuoteEntry(BaseModel):
    quote: str = Field(default="", description="The quote text.")
    source: str = Field(default="", description="The source of the quote.")


class WikiQuoteCrawler(Crawler):
    base_url: str = Field(default="https://zh.wikiquote.org/wiki/{title}")
    whitelist: List[str] = Field(
        default=["语录", "語錄", "名言", "作品摘录"],
        description="白名单，只爬取白名单内的标题",
    )
    blacklist: List[str] = Field(
        default=["模板", "分类", "帮助", "MediaWiki", "Wikiquote", "参见", "参考文献"],
        description="黑名单，不爬取黑名单内的标题",
    )
    prompt: str = Field(
        default="Please evaluate the following content, and extract the quote and source(if applicable) from the given text only. Do not add, infer, or supplement any information that is not explicitly present in the given text. Do not include any additional commentary or background information that follows.",
    )

    def format_url(self, jar: CookieJar) -> str:
        return self.base_url.format(title=jar.name)

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

    def parse_item(self, element) -> Cookie:
        # 提取名言部分
        span_element = element.find("span")
        source_element = element.find("dd")
        if not source_element:
            source_element = element.find("li")

        # 获取名言文本并清理
        quote_text = ""
        for content in element.contents:
            if content == span_element:
                continue
            if isinstance(content, str):
                quote_text += content.strip()
            elif content.name == "a":
                quote_text += content.text.strip()
            elif content.name == "br":
                quote_text += "\n"
            elif content.name == "b":
                quote_text += content.text.strip()
            elif content.name == "sup":
                continue

        # 获取来源文本并清理
        if source_element:
            source_text = ""
            for content in source_element.contents:
                if isinstance(content, str):
                    source_text = content.strip()
                elif content.name == "a":
                    source_text = content.text.strip()
                elif content.name == "br":
                    source_text = "\n"
                elif content.name == "b":
                    source_text = content.text.strip()
                elif content.name == "sup":
                    continue
            source_text = (
                source_text.strip().replace("——", "").replace("出自", "").strip()
            )
        else:
            source_text = ""

        return Cookie(
            content=quote_text,
            source=source_text,
        )

    def get_chain(self, model_name: str = "openai:gpt-4o") -> Any:
        logger.debug(f"Create chain => model: {model_name}")
        return get_llm_chain(
            prompt_template=self.prompt, model_name=model_name, cls=WikiQuoteEntry
        )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []
        cookies_without_source = []
        jar.link = self.format_url(jar)
        soup = self.get_page(jar.link)
        if not soup:
            return cookies

        for item in self.parse_list(soup):
            cookie = self.parse_item(item)
            if cookie.content:
                cookie.link = jar.link
                if not cookie.source:
                    cookies_without_source.append(cookie)
                else:
                    cookies.append(cookie)

        # find the source for quotes without source by using the language model
        quotes = self.get_chain(jar.model_name).batch(
            [{"content": cookie.content} for cookie in cookies_without_source],
            return_exceptions=True,
        )
        for i, quote in enumerate(quotes):
            cookie = cookies_without_source[i]
            if isinstance(quote, WikiQuoteEntry):
                cookie.content = quote.quote.strip()
                cookie.source = quote.source.strip()

                if (
                    jar.lang.startswith("zh")
                    and cookie.source
                    and "《" not in cookie.source
                ):
                    cookie.source = f"《{cookie.source}》"

            elif isinstance(quote, Exception):
                err_msg = str(quote)
                logger.warning(
                    f"Failed to extract source for the quote: {cookie.content} => {quote}"
                )
                if "DataInspectionFailed" not in err_msg:
                    remove_from_cache(cookie.content)
                cookie.source = jar.name
            else:
                cookie.source = jar.name

            cookies.append(cookie)

        # add author name to the source if it's not already there
        for cookie in cookies:
            if jar.name not in cookie.source:
                cookie.source = f"{cookie.source} {jar.name}"
                cookie.source = cookie.source.strip()
        logger.info(f"爬取 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        crawler = WikiQuoteCrawler()
        return crawler.crawl(jar)
