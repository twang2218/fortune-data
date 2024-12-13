from typing import List

from common import Cookie, CookieJar
from loguru import logger
from pydantic import Field

from .crawler import Crawler


class MingJuCrawler(Crawler):
    base_url: str = Field(
        default="https://www.gushiwen.cn/mingjus/default.aspx?page={page}&{key}={category}"
    )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        _, _, _, key = jar.extractor.split(".")

        # 爬取名句
        cookies = []
        for page in range(1, self.max_page):
            jar.link = self.base_url.format(key=key, category=jar.name, page=page)
            body = self.get_page(jar.link)
            if not body:
                continue

            # 获取当前页面所有名句链接
            for element in self.parse_list(body):
                cookie = self.parse_item(element)
                if not cookie:
                    logger.warning(f"无法解析名句 {element}")
                    print("?", end="", flush=True)
                    continue
                else:
                    cookie.source = jar.name
                    cookies.append(cookie)
                    print(".", end="", flush=True)
            # print()
            # 获取下一页链接
            next_page = body.find("a", class_="amore")
            if not next_page or not next_page.has_attr("href"):
                # 如果没有下一页，结束爬取
                logger.debug(f"当前页 {page} 无下一页，结束爬取。")
                break
        logger.info(f"爬取 《{jar.name}》 完成, 共爬取 {len(cookies)} 条。")
        return cookies

    def parse_item(self, element) -> Cookie:
        if not element:
            return None
        try:
            links = element.find_all("a")
            if links and len(links) > 0:
                cookie = Cookie(
                    title=self.get_content(links[1]) if len(links) > 1 else "",
                    author="",
                    content=self.get_content(links[0]),
                    source="",
                    link=self.get_link(links[0]),
                )
                if cookie.title and "《" not in cookie.title:
                    cookie.title = f"《{cookie.title}》"
                return cookie
            else:
                return None
        except Exception as e:
            logger.error(f"Error parsing cookie: {str(e)}")
            return None

    def parse_list(self, element) -> List:
        elements = []
        lefts = element.find_all("div", class_="left")
        for left in lefts:
            div_cookies = left.find_all("div", class_="cont")
            for div_cookie in div_cookies:
                elements.append(div_cookie)
        return elements

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", "gushiwen", "mingju", _:
                crawler = MingJuCrawler()
                return crawler.crawl(jar)
            case _:
                raise ValueError(f"MingJuCrawler: Invalid extractor: {jar.extractor}")


class GuShiCrawler(Crawler):
    base_url: str = Field(default="https://www.gushiwen.cn/gushi/{key}.aspx")

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        logger.info(f"开始爬取 《{jar.name}》")
        _, _, _, key = jar.extractor.split(".")

        # 爬取诗词
        jar.link = self.base_url.format(key=key)
        body = self.get_page(jar.link)

        cookies = []
        for element in self.parse_list(body):
            link = self.get_link(element)
            link_body = self.get_page(link)
            cookie = self.parse_item(link_body)
            if not cookie:
                logger.warning(f"无法解析诗词 {link}")
                self.remove_link_from_cache(link)
                print("?", end="", flush=True)
            else:
                cookie.link = link
                cookie.source = jar.name
                cookies.append(cookie)
                print(".", end="", flush=True)
        #     if len(cookies) % 50 == 0:
        #         print()
        # print()

        logger.info(f"爬取 《{jar.name}》 完成, 共爬取 {len(cookies)} 条。")
        return cookies

    def parse_item(self, element) -> Cookie:
        if not element:
            return None
        try:
            cookie = Cookie(
                title=self.get_content(element.find("h1")),
                author=self.get_content(element.find("p", class_="source")),
                content=self.get_content(element.find("div", class_="contson")),
                source="",
                link="",
            )
            if cookie.title and "《" not in cookie.title:
                cookie.title = f"《{cookie.title}》"
            return cookie
        except Exception as e:
            logger.error(f"Error parsing cookie: {str(e)}")
            return None

    def parse_list(self, element) -> List:
        if not element:
            return []
        section = element.find("div", class_="sons")
        if not section:
            return []
        links = section.find_all("a")
        return [link for link in links if link.has_attr("href")]

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", "gushiwen", "gushi", _:
                crawler = GuShiCrawler()
                return crawler.crawl(jar)
            case _:
                raise ValueError(f"GuShiCrawler: Invalid extractor: {jar.extractor}")


class ShiWenCrawler(GuShiCrawler):
    base_url: str = Field(
        default="https://www.gushiwen.cn/shiwens/default.aspx?{key}={category}"
    )

    def crawl(self, jar: CookieJar) -> List[Cookie]:
        """爬取诗文"""
        logger.info(f"开始爬取 《{jar.name}》")
        _, _, _, key = jar.extractor.split(".")

        # 爬取诗词
        jar.link = self.base_url.format(key=key, category=jar.name)
        body = self.get_page(jar.link)

        cookies = []
        for element in self.parse_list(body):
            link = self.get_link(element)
            link_body = self.get_page(link)
            cookie = self.parse_item(link_body)
            if not cookie:
                logger.warning(f"无法解析诗词 {link}")
                self.remove_link_from_cache(link)
                print("?", end="", flush=True)
                # continue
            else:
                cookie.link = link
                cookie.source = jar.name
                cookies.append(cookie)
                print(".", end="", flush=True)
        #     if len(cookies) % 50 == 0:
        #         print()
        # print()

        logger.info(f"爬取 《{jar.name}》 完成, 共爬取 {len(cookies)} 条。")
        return cookies

    def parse_list(self, element) -> List:
        if not element:
            return []
        section = element.find("div", class_="typecont")
        if not section:
            return []
        links = section.find_all("a")
        return [link for link in links if link.has_attr("href")]

    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", "gushiwen", "shiwen", _:
                crawler = ShiWenCrawler()
                return crawler.crawl(jar)
            case _:
                raise ValueError(f"ShiWenCrawler: Invalid extractor: {jar.extractor}")


class GushiwenCrawler(Crawler):
    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        parts = jar.extractor.split(".")
        match parts[2]:
            case "mingju":
                return MingJuCrawler.extract(jar)
            case "gushi":
                return GuShiCrawler.extract(jar)
            case "shiwen":
                return ShiWenCrawler.extract(jar)
            case _:
                raise ValueError(f"GushiwenCrawler: Invalid extractor: {jar.extractor}")
