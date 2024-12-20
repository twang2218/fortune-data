import copy
import re
from typing import Callable, List, Tuple

from common import Agent, Cookie, CookieJar
from loguru import logger
from pydantic import BaseModel, Field

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
        default=["See also", "References", "External links"],
        description="blacklist, never crawl the title in the black list",
    )
    prompt: str = Field(
        default="Please evaluate the following content, and extract the quote and source(if applicable) from the given text only. Do not add, infer, or supplement any information that is not explicitly present in the given text. Do not include any additional commentary or background information that follows.",
    )
    source_leadings: List[str] = Field(
        default=["--", "-", "–", "~", "—"],
        description="The leading characters to remove from the source text.",
    )
    parentheses_left: List[str] = Field(
        default=[r"\[", r"\("],
        description="The left parentheses to remove from the source text.",
    )
    parentheses_right: List[str] = Field(
        default=[r"\]", r"\)"],
        description="The right parentheses to remove from the source text.",
    )
    quotation_marks_left: List[str] = Field(
        default=["'", "“", "‘"],
        description="The left quotation marks to remove from the quote text.",
    )
    quotation_marks_right: List[str] = Field(
        default=["'", "”", "’"],
        description="The right quotation marks to remove from the quote text.",
    )
    css_body: str = Field(
        default="div.mw-parser-output",
        description="The CSS selector for the body of the page.",
    )
    css_header: str = Field(
        default="div.mw-heading2 h2",
        description="The CSS selector for the headers in the page.",
    )
    css_items: List[Tuple[str, str]] = Field(
        default=[("li", "> ul > li")],
        description="The CSS selector for the items in the page.",
    )
    parse_element_text_whitelist: List[str] = Field(
        default=["a", "b", "i", "strong"],
        description="The tags to parse when parsing text of the element",
    )

    def format_url(self, jar: CookieJar) -> str:
        parts = jar.extractor.split(".")
        lang = parts[2]
        return self.base_url.format(title=jar.name.replace(" ", "_"), lang=lang)

    def parse_list(self, soup) -> List[str]:
        quotes = []

        selectors = [f"{self.css_body} {self.css_header}"] + [
            f"{self.css_body} {item[1]}" for item in self.css_items
        ]
        selector = ", ".join(selectors)
        current_title = ""
        for item in soup.select(selector):
            if item.name == "h2":
                current_title = item.text
                continue
            if current_title not in self.blacklist:
                for tag, _ in self.css_items:
                    if item.name == tag:
                        quotes.append(item)
        return quotes

    def parse_element_text(self, element) -> str:
        if not element:
            return ""
        elif isinstance(element, str):
            return element

        text = ""
        for content in element.contents:
            if isinstance(content, str):
                text += content
            elif content.name == "br":
                text += "\n"
            elif content.name == "p":
                text += self.parse_element_text(content) + "\n"
            elif content.name in self.parse_element_text_whitelist:
                text += self.parse_element_text(content)
            else:
                # skip other tags
                continue
        # clean up
        text = text.replace("\xa0", " ").replace("\u200b", "").replace("\u00a0", " ")
        return text

    def parse_item(self, element) -> Cookie:
        content = self.parse_content(element)
        source = self.parse_source(element)

        if content and not source:
            # 尝试从 content 中提取 source
            content, source = self.parse_source_from_content(content)

        return Cookie(
            content=content.strip(),
            source=source.strip(),
        )

    def parse_content(self, element) -> str:
        content = self.parse_element_text(element) if element else ""
        for leading in self.source_leadings:
            if content.strip().startswith(leading):
                # it's a source, not a quote
                return ""
        return content.strip()

    def get_source_find_candidates(self, element) -> List:
        candidates = []
        if element.next_sibling:
            candidates.append(element.next_sibling)
        if element.parent and element.parent.next_sibling:
            candidates.append(element.parent.next_sibling)
        return candidates

    def get_source_finders(self) -> List[Callable]:
        def find_source_parent_dd(e):
            candidates = self.get_source_find_candidates(e)
            for candidate in candidates:
                # select the most inner dd element
                if candidate.name == "dl" and candidate.select_one(
                    "dd:not(:has(> dl))"
                ):
                    return candidate.select_one("dd:not(:has(> dl))")
            return None

        def find_source_parent_p(e):
            candidates = self.get_source_find_candidates(e)
            for candidate in candidates:
                if candidate.name == "p" and len(candidate.text.strip()) < 50:
                    return candidate
            return None

        return [
            lambda e: e.find("dd"),
            lambda e: e.find("li"),
            find_source_parent_dd,
            find_source_parent_p,
        ]

    def parse_source(self, element) -> str:
        source_element = None
        for finder in self.get_source_finders():
            source_element = finder(element)
            if source_element:
                break
        if not source_element:
            return ""
        source = self.parse_element_text(source_element) if source_element else ""
        if source:
            for leading in self.source_leadings:
                source = source.strip().lstrip(leading).strip()
        return source.strip()

    def get_parse_source_from_content_patterns(self) -> List[str]:
        patterns = []

        # History would be an excellent thing if only it were true. (Leo Tolstoy)
        left = "".join([f"{p}" for p in self.parentheses_left])
        right = "".join([f"{p}" for p in self.parentheses_right])
        pattern = r"^(.*?)(?:[" + left + r"](.*?)[" + right + r"])\s*$"
        patterns.append(pattern)

        # 31. History would be an excellent thing if only it were true. ~ Leo Tolstoy
        leading = "|".join(self.source_leadings)
        leading = r"(?:\s*(?:" + leading + r"))"
        index = r"(?:\d+\.?\s+)?"
        group = r"(.*?)"
        pattern = r"^" + index + group + leading + r"\s+" + group + leading + r"?\s*$"
        patterns.append(pattern)

        return patterns

    def parse_source_from_content(self, content: str) -> Tuple[str, str]:
        for pattern in self.get_parse_source_from_content_patterns():
            m = re.match(pattern, content, re.MULTILINE | re.DOTALL)
            if m:
                quote = m.group(1).strip()
                source = m.group(2).strip()
                if quote and source:
                    return quote, source

        logger.debug(f"Failed to extract source from content: {content}")
        return content, ""

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        cookies = []
        jar.link = self.format_url(jar)
        logger.info(f"开始爬取 [{jar.lang}] 《{jar.name}》: {jar.link}")
        soup = self.get_page(jar.link)
        if not soup:
            return cookies

        for item in self.parse_list(soup):
            cookie = self.parse_item(item)
            if cookie.content:
                cookie.link = jar.link
                cookies.append(cookie)

        cookies = self.process_cookies(cookies, jar)

        logger.info(f"爬取 [{jar.lang}] 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies

    def process_content_by_llm(
        self, cookies: List[Cookie], jar: CookieJar
    ) -> List[Cookie]:
        agent = Agent(prompt=self.prompt, base_model=jar.model_name, cls=Quote)
        cookies_with_source = [cookie for cookie in cookies if cookie.source]
        cookies_without_source = [cookie for cookie in cookies if not cookie.source]
        if len(cookies_without_source) == 0:
            return cookies
        logger.debug(
            f"Agent({jar.model_name}): '{jar.name}': cookies_without_source: {len(cookies_without_source)} / total: {len(cookies)}"
        )
        quotes = agent.process([cookie.content for cookie in cookies_without_source])
        for i, quote in enumerate(quotes):
            cookie = cookies_without_source[i]
            if isinstance(quote, Quote) and quote.source.strip():
                cookie.content = quote.quote.strip()
                cookie.source = quote.source.strip()
            else:
                cookie.source = jar.name
            cookies_with_source.append(cookie)
        return cookies_with_source

    def process_source(self, cookies: List[Cookie], jar: CookieJar) -> List[Cookie]:
        for cookie in cookies:
            if not jar.is_category and jar.name not in cookie.source:
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
        parts = jar.extractor.split(".")
        match parts[0], parts[1], parts[2]:
            case "crawler", "wikiquote", "en":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyEnWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = EnWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "es":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyEsWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = EsWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "de":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyDeWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = DeWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "fr":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyFrWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = FrWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "ja":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyJaWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = JaWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "ru":
                if len(parts) > 3 and parts[3] == "daily":
                    crawler = DailyRuWikiQuoteCrawler()
                    return crawler.crawl(jar)
                else:
                    crawler = RuWikiQuoteCrawler()
                    return crawler.crawl(jar)
            case "crawler", "wikiquote", "zh":
                crawler = ZhWikiQuoteCrawler()
                return crawler.crawl(jar)
            case "crawler", "wikiquote", _:
                crawler = WikiQuoteCrawler()
                return crawler.crawl(jar)
            case _:
                raise ValueError(
                    f"WikiQuoteCrawler: Invalid extractor: {jar.extractor}"
                )


class EnWikiQuoteCrawler(WikiQuoteCrawler):
    pass


class DailyEnWikiQuoteCrawler(EnWikiQuoteCrawler):
    base_url: str = Field(
        default="https://en.wikiquote.org/wiki/Wikiquote:Quote_of_the_Day"
    )
    css_items: List[Tuple[str, str]] = Field(
        default=[
            ("dd", "> dl > dd"),
            ("li", "> ol > li"),
        ]
    )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []

        jar.link = self.base_url
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


class EsWikiQuoteCrawler(WikiQuoteCrawler):
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + [
            "Categoría",
            "Enlaces externos",
            "Referencias",
            "Véase también",
            "Bibliografía",
        ],
    )

    def parse_content(self, element) -> str:
        content = super().parse_content(element)
        if "«" in content and "»" in content:
            content = content.replace("«", "").replace("»", "")
        return content.strip()


class DailyEsWikiQuoteCrawler(EsWikiQuoteCrawler):
    base_url: str = Field(
        default="https://es.wikiquote.org/wiki/Wikiquote:Archivo_de_la_Frase_célebre_del_día"
    )

    css_items: List[Tuple[str, str]] = Field(
        default=[
            ("li", "> ul > li"),
            ("div", "> div#toc"),
        ],
        description="The CSS selector for the items in the page.",
    )

    def parse_content(self, element) -> str:
        rows = element.select("tbody tr")
        if not rows:
            return ""

        # the first row is the quote
        row = rows[0]
        for element in row.select("td div:not(:has(> span))"):
            if element.text.strip():
                content = super().parse_content(element)
                return content
        return ""

    def get_source_finders(self) -> List[Callable]:
        def find_source_parent_td(e):
            rows = e.select("tbody tr")
            if not rows:
                return None
            if len(rows) < 2:
                return None
            # the second row is the source
            row = rows[1]
            for element in row.select("td div"):
                if element.text.strip():
                    return element
            return None

        def find_source_parent_div(e):
            rows = e.select("td div:not(:has(> span))")
            if not rows:
                return None
            if len(rows) > 1:
                return rows[1]
            return None

        finders = super().get_source_finders()
        finders.insert(0, find_source_parent_td)
        finders.insert(1, find_source_parent_div)
        return finders

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []

        jar.link = self.base_url
        soup = self.get_page(jar.link)
        if not soup:
            return cookies

        for item in soup.select("div.mw-parser-output > p > a"):
            url = item.get("href")
            if not url:
                continue
            # if 'junio/2005' not in url:
            # if 'octubre/2007' not in url:
            #     continue
            logger.debug(f"爬取 sub_page: {url}")
            url = self.get_link(url)
            sub_page = self.get_page(url)
            if not sub_page:
                continue
            for sub_item in self.parse_list(sub_page):
                cookie = self.parse_item(sub_item)
                if cookie.content:
                    cookie.link = url
                    cookies.append(cookie)

        cookies = self.process_cookies(cookies, jar)

        logger.info(f"爬取 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies


class DeWikiQuoteCrawler(WikiQuoteCrawler):
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + ["Literatur", "Weblinks", "Einzelnachweise", "Siehe auch"],
    )
    source_leadings: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["source_leadings"].default
        + ["aus", "von", "zitiert in", "zitiert nach"],
    )

    def get_parse_source_from_content_patterns(self) -> List[str]:
        patterns = super().get_parse_source_from_content_patterns()

        # "Adel verpflichtet." (Noblesse oblige) - nach Pierre-Marc-Gaston de Lévis, Maximes et réflections
        leadings = "|".join(self.source_leadings)
        leadings = f"(?:{leadings})?"
        comments = r"(?:\(.*?\))?"
        pattern = (
            r"^\"(.*?)\"\s*"
            + comments
            + r"\s*"
            + leadings
            + r"\s*(.*?)\s*"
            + comments
            + r"\s*$"
        )
        patterns.insert(0, pattern)

        return patterns


class DailyDeWikiQuoteCrawler(DeWikiQuoteCrawler):
    base_url: str = Field(
        default="https://de.wikiquote.org/wiki/Vorlage:Zitat_des_Tages/{title}"
    )
    sub_titles: List[str] = Field(
        ["Archiv_2004", "Archiv_2005", "Archiv_2006", "Archiv_2007", "Archiv_2008"]
    )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []

        jar.link = self.base_url.format(title="Archiv")
        for sub_title in self.sub_titles:
            url = self.base_url.format(title=sub_title)
            soup = self.get_page(url)
            if not soup:
                continue

            for item in self.parse_list(soup):
                cookie = self.parse_item(item)
                if cookie.content:
                    cookie.link = url
                    cookies.append(cookie)

        cookies = self.process_cookies(cookies, jar)

        logger.info(f"爬取 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies


class FrWikiQuoteCrawler(WikiQuoteCrawler):
    whitelist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["whitelist"].default
        + ["Citations", "Références", "Voir aussi", "Liens externes"],
    )
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + ["Catégorie", "Portail", "Projet", "Modèle", "Articles connexes"],
    )
    css_items: List[Tuple[str, str]] = Field(
        default=[
            ("div", ".citation"),
        ]
    )

    def get_source_finders(self) -> List[Callable]:
        def find_source_parent_ref(e):
            if e.parent:
                candidates = e.parent.select(".ref")
                for candidate in candidates:
                    if (
                        candidate.sourceline >= e.sourceline
                        and candidate.sourceline - e.sourceline < 5
                    ):
                        return candidate
            return None

        finders = super().get_source_finders()
        finders.insert(0, find_source_parent_ref)
        return finders


class DailyFrWikiQuoteCrawler(FrWikiQuoteCrawler):
    base_url: str = Field(
        default="https://fr.wikiquote.org/wiki/Wikiquote:Citation_du_jour"
    )
    css_items: List[Tuple[str, str]] = Field(
        default=[
            ("div", "div div div:not(:has(p))"),
        ],
        description="The CSS selector for the items in the page.",
    )
    parse_element_text_whitelist: List[str] = Field(
        default=FrWikiQuoteCrawler.model_fields["parse_element_text_whitelist"].default
        + ["span", "div"]
    )

    def parse_content(self, element) -> str:
        if element.find("i"):
            element = element.find("i")
        return super().parse_content(element)

    def get_source_finders(self) -> List[Callable]:
        def find_source_a(e):
            if e.find("a"):
                return e.find("a")
            return None

        def find_source_text(e):
            e = copy.deepcopy(e)
            content_element = e.find("i")
            if content_element:
                content_element.decompose()
                return e
            return None

        finders = super().get_source_finders()
        finders.insert(0, find_source_a)
        finders.insert(1, find_source_text)
        return finders

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        cookies = []

        jar.link = self.base_url
        soup = self.get_page(jar.link)
        if not soup:
            return cookies

        for item in soup.select("div.mw-parser-output > ul > li > a"):
            url = item.get("href")
            if not url:
                continue
            logger.debug(f"爬取 sub_page: {url}")
            url = self.get_link(url)
            sub_page = self.get_page(url)
            if not sub_page:
                continue
            for sub_item in self.parse_list(sub_page):
                cookie = self.parse_item(sub_item)
                if cookie.content:
                    cookie.link = url
                    cookies.append(cookie)

        cookies = self.process_cookies(cookies, jar)

        logger.info(f"爬取 《{jar.name}》完成，共 {len(cookies)} 条名言")
        return cookies


class JaWikiQuoteCrawler(WikiQuoteCrawler):
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + [
            "関連項目",
            "参考文献",
            "外部リンク",
            "脚注",
            "出典",
            "注釈",
            "関連項目・外部リンク",
            "関連項目、外部リンク",
            "関連語句",
        ],
    )

    def get_source_finders(self) -> List[Callable]:
        # disable source finding
        return []

    def get_parse_source_from_content_patterns(self) -> List[str]:
        patterns = super().get_parse_source_from_content_patterns()

        # 今は信、望、愛、此の三つのもの存す。其中に最も大いなる者は愛なり。--パウロ『コリントの信徒への手紙一』（コリント前書）13:13、正教会訳。
        leadings = "|".join(self.source_leadings)
        leadings = f"(?:{leadings})"
        group = r"(.*?)"
        pattern = r"^" + group + r"\s*" + leadings + r"\s*" + group + r"\s*$"
        patterns.insert(0, pattern)

        return patterns


class DailyJaWikiQuoteCrawler(JaWikiQuoteCrawler):
    pass


class RuWikiQuoteCrawler(WikiQuoteCrawler):
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + ["См. также", "Примечания", "Литература", "Ссылки"],
    )
    css_items: List[Tuple[str, str]] = Field(
        default=[
            ("table", "table.q"),
            ("li", "> ul > li"),
        ]
    )

    def parse_content(self, element) -> str:
        content_element = element.select_one("tr.q-text .poem")
        if not content_element:
            content_element = element
        return super().parse_content(content_element)

    def get_source_finders(self) -> List[Callable]:
        finders = super().get_source_finders()

        def find_source_td(e):
            elements = e.select("tr.q-author td")
            for element in elements:
                if len(element.text) > 5:
                    return element
            return None

        finders.insert(0, find_source_td)
        return finders


class DailyRuWikiQuoteCrawler(RuWikiQuoteCrawler):
    def format_url(self, jar: CookieJar) -> str:
        return self.base_url.format(lang="ru", title="Шаблон:Избранная_цитата/Архив")


class ZhWikiQuoteCrawler(WikiQuoteCrawler):
    whitelist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["whitelist"].default
        + ["语录", "語錄", "名言", "作品摘录"],
    )
    blacklist: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["blacklist"].default
        + [
            "参见",
            "参考文献",
            "注释及参考资料",
            "链接",
            "外部链接",
            "相关条目",
            "相关人士语录",
            "相关语录",
        ],
    )
    source_leadings: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["source_leadings"].default
        + ["——", "出自", "引自", "来源", "摘自"],
    )
    parentheses_left: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["parentheses_left"].default
        + ["（", "【", "《"],
    )
    parentheses_right: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["parentheses_right"].default
        + ["）", "】", "》"],
    )
    quotation_marks_left: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["quotation_marks_left"].default
        + ["「", "『", "《", "【", "〈", "〔", "〖"],
    )
    quotation_marks_right: List[str] = Field(
        default=WikiQuoteCrawler.model_fields["quotation_marks_right"].default
        + ["」", "』", "》", "】", "〉", "〕", "〗"],
    )

    def process_source(self, cookies: List[Cookie], jar: CookieJar) -> List[Cookie]:
        for cookie in cookies:
            if cookie.source:
                contains_quotation_mark = False
                for mark in self.quotation_marks_left + self.quotation_marks_right:
                    if mark in cookie.source:
                        contains_quotation_mark = True
                        break
                if not contains_quotation_mark:
                    cookie.source = f"《{cookie.source}》"

        cookies = super().process_source(cookies, jar)

        return cookies
