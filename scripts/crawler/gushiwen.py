import sys
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
from urllib.parse import urljoin
from dataclasses import dataclass

from loguru import logger

@dataclass
class Cookie:
    title: str
    author: str
    content: str
    source: str
    type: str
    content_link: str
    source_link: str

    def to_json(self):
        return json.dumps(
            {
                "type": self.type,
                "title": self.title,
                "author": self.author,
                "content": self.content,
                "source": self.source,
                "content_link": self.content_link,
                "source_link": self.source_link,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Cookie(
            type=data["type"],
            title=data["title"],
            author=data["author"],
            content=data["content"],
            source=data["source"],
            content_link=data["content_link"],
            source_link=data["source_link"],
        )
    
    @staticmethod
    def from_dict(data):
        return Cookie(
            title=data["title"],
            author=data["author"],
            content=data["content"],
            source=data["source"],
            content_link=data["content_link"],
            source_link=data["source_link"],
            type=data["type"],
        )
    
    def __str__(self):
        if self.type == "mingju":
            return f"{self.content}\n -- {self.source}\n%"
        else:
            return f"《{self.title}》 -- {self.author}\n{self.content}\n%"

class Parser:
    def __init__(self, base_url: str, parser_type: str):
        self.base_url = base_url
        self.parser_type = parser_type

    def get_text(self, element):
        """获取文本内容"""
        if not element:
            return None
        # 保留换行信息
        for br in element.find_all("br"):
            br.replace_with("\n")
        for p in element.find_all("p"):
            p.replace_with("\n" + p.text)
        return element.text.strip()

    def get_link(self, link):
        if link and link.has_attr("href"):
            return urljoin(self.base_url, link["href"])
        return None

    def parse_item(self, element) -> Cookie:
        raise NotImplementedError

    def parse_list(self, element) -> list[str]:
        raise NotImplementedError
    

class MingJuParser(Parser):
    def __init__(self, base_url: str, parser_type: str = "mingju"):
        super().__init__(base_url, parser_type)

    def parse_item(self, element) -> Cookie:
        if not element:
            return None
        try:
            links = element.find_all("a")
            if links and len(links) == 2:
                cookie = Cookie(
                    title=self.get_text(links[1]),
                    author="",
                    content=self.get_text(links[0]),
                    source="",
                    content_link=self.get_link(links[0]),
                    source_link=self.get_link(links[1]),
                    type=self.parser_type,
                )
                return cookie
            else:
                return None
        except Exception as e:
            print(f"Error parsing cookie: {str(e)}")
            return None

class GuShiParser(Parser):
    def __init__(self, base_url: str, parser_type: str = "gushi"):
        super().__init__(base_url, parser_type)

    def parse_item(self, element) -> Cookie:
        if not element:
            return None
        try:
            cookie = Cookie(
                title=self.get_text(element.find("h1")),
                author=self.get_text(element.find("p", class_="source")),
                content=self.get_text(element.find("div", class_="contson")),
                source="",
                content_link="",
                source_link="",
                type=self.parser_type,
            )
            return cookie
        except Exception as e:
            print(f"Error parsing cookie: {str(e)}")
            return None
        
    def parse_list(self, element) -> list[str]:
        if not element:
            return []
        section = element.find("div", class_="sons")
        if not section:
            return []
        links = section.find_all("a")
        return [self.get_link(link) for link in links]

class ShiWenParser(GuShiParser):
    def __init__(self, base_url: str, parser_type: str = "shiwen"):
        super().__init__(base_url, parser_type)

    def parse_list(self, element) -> list[str]:
        if not element:
            return []
        section = element.find("div", class_="typecont")
        if not section:
            return []
        links = section.find_all("a")
        return [self.get_link(link) for link in links]

class Crawler:
    def __init__(self, base_url: str = ""):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        self.base_url = base_url
        self.cache = set()
        self.max_page = 100

    def get_page(self, url):
        """获取页面内容并返回 BeautifulSoup 对象"""
        try:
            # 添加随机延迟
            time.sleep(random.uniform(1, 3))
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
        
    def load(self, file_link) -> list[Cookie]:
        """加载已保存的数据"""
        self.cache = set()
        cookies = []
        if os.path.exists(file_link):
            with open(file_link, "r", encoding="utf-8") as f:
                for line in f:
                    cookie = Cookie.from_json(line)
                    cookies.append(cookie)
                    self.cache.add(cookie.content_link)
            logger.debug(f"加载了已保存的数据 {len(cookies)} 条")
        
        return cookies

    def store(self, filename, cookie):
        """保存数据"""
        if not cookie:
            self.print("?")
        elif cookie.content_link in self.cache:
            self.print(".")
        else:
            with open(filename, "a", encoding="utf-8") as f:
                f.write(cookie.to_json() + "\n")
            self.cache.add(cookie.content_link)
            print(cookie)

    def print(self, text):
        print(text, end="", flush=True)
        sys.stdout.flush()
    

class MingJuCrawler(Crawler):
    def __init__(self, base_url: str = "https://www.gushiwen.cn/mingjus/default.aspx?page={page}&tstr={category}&astr=&cstr=&xstr="):
        super().__init__(base_url=base_url)
        self.parser = MingJuParser(self.base_url)
        self.saved_links = set()
        self.data_dir = "data/mingju"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def crawl(self, category: str):
        logger.info(f"开始爬取 《{category}》")

        # 加载已保存的名句链接
        filename = f"{self.data_dir}/{category}.jsonl"
        cookies = self.load(filename)

        # 爬取名句
        for page in range(1, self.max_page):
            url = self.base_url.format(category=category, page=page)
            soup = self.get_page(url)
            if not soup:
                continue

            # 获取当前页面所有名句链接
            cookies = soup.find_all("div", class_="cont")
            for cookie in cookies:
                item = self.parser.parse_item(cookie)
                if not item:
                    # logger.debug(f"无法解析名句 {cookie}")
                    self.print("?")
                    continue
                item.source = category
                item.source_link = url
                self.store(filename, item)
            print()

            # 获取下一页链接
            next_page = soup.find("a", class_="amore")
            if not next_page or not next_page.has_attr("href"):
                # 如果没有下一页，结束爬取
                logger.debug(f"当前页 {page} 无下一页")
                break
        logger.info(f"爬取 《{category}》 完成, 共爬取 {len(self.cache)} 条。")

class GuShiCrawler(Crawler):
    def __init__(self, base_url: str = "https://www.gushiwen.cn/gushi/{category}.aspx"):
        super().__init__(base_url=base_url)
        self.parser = GuShiParser(self.base_url)
        self.saved_links = set()
        self.data_dir = "data/gushi"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def crawl(self, category: str, key: str):
        logger.info(f"开始爬取 《{category}》")
        
        # 加载已保存的诗词链接
        filename = f"{self.data_dir}/{category}.jsonl"
        cookies = self.load(filename)

        # 爬取诗词
        url = self.base_url.format(category=key)
        body = self.get_page(url)
        links = self.parser.parse_list(body)
        if not links or len(links) == 0:
            logger.error(f"无法获取 {url}")
            return
        
        for link in links:
            if link in self.cache:
                self.print(".")
                continue
            else:
                body = self.get_page(link)
                item = self.parser.parse_item(body)
                if not item:
                    logger.debug(f"无法解析诗词 {link}")
                    continue

                item.content_link = link
                item.source = category
                item.source_link = url

                self.store(filename, item)
            print()

        logger.info(f"爬取 《{category}》 完成, 共爬取 {len(self.cache)} 条。")

class ShiWenCrawler(GuShiCrawler):
    def __init__(self, base_url: str = "https://www.gushiwen.cn/shiwens/default.aspx?cstr={category}"):
        super().__init__(base_url=base_url)
        self.parser = ShiWenParser(self.base_url)
        self.data_dir = "data/shiwen"
        os.makedirs(self.data_dir, exist_ok=True)

    def crawl(self, category: str):
        """爬取诗文"""
        logger.info(f"开始爬取 《{category}》")
        
        # 加载已保存的诗词链接
        filename = f"{self.data_dir}/{category}.jsonl"
        cookies = self.load(filename)

        # 爬取诗词
        url = self.base_url.format(category=category)
        body = self.get_page(url)
        links = self.parser.parse_list(body)
        if not links or len(links) == 0:
            logger.error(f"无法获取 {url}")
            return
        
        for link in links:
            if link in self.cache:
                self.print(".")
                continue
            else:
                body = self.get_page(link)
                item = self.parser.parse_item(body)
                if not item:
                    logger.debug(f"无法解析诗词 {link}")
                    continue

                item.content_link = link
                item.source = category
                item.source_link = url

                self.store(filename, item)
            print()

        logger.info(f"爬取 《{category}》 完成, 共爬取 {len(self.cache)} 条。")

def main():
    logger.level("DEBUG")
    mingju_titles = [
        # 哲学思想
        "论语",
        "大学",
        "孟子",
        "中庸",
        "荀子",
        "易传",
        "老子",
        "庄子",
        "韩非子",
        "鬼谷子",
        "管子",
        "墨子",
        "商君书",
        "淮南子",
        "三十六计",
        "孙子兵法",
        # 历史类
        "左传",
        "尚书",
        "吕氏春秋",
        "战国策",
        "史记",
        "汉书",
        "后汉书",
        "晋书",
        "资治通鉴",
        "贞观政要",
        # 教育类
        "了凡四训",
        "弟子规",
        "朱子家训",
        "孔子家语",
        "颜氏家训",
        "三字经",

        "格言联璧",
        "小窗幽记",
        "幼学琼林",
        "随园诗话",

        "菜根谭",
        "增广贤文",
        "围炉夜话",
        "醒世恒言",
        "警世通言",

        # 文学类
        ## 小说
        "红楼梦",
        "西游记",
        "水浒传",
        "三国演义",
        "儒林外史",
        "镜花缘",
        "济公全传",
        "官场现形记",
        ## 诗歌
        "诗经",
        ## 散文
        "文心雕龙",
    ]
    
    gushi_titles = [
        ("tangshi", "唐诗三百首"),
        ("sanbai", "古诗三百首"),
        ("songsan", "宋词三百首"),
        ("chuci", "楚辞"),
        ("shijing", "诗经"),
        ("yuefu", "乐府诗集"),
    ]

    shiwen_title = [
        "近现代",
    ]
    
    mingju_crawler = MingJuCrawler()
    for title in mingju_titles:
        mingju_crawler.crawl(title)
    
    gushi_crawler = GuShiCrawler()
    for (key, name) in gushi_titles:
        gushi_crawler.crawl(name, key)
    
    shiwen_crawler = ShiWenCrawler()
    for title in shiwen_title:
        shiwen_crawler.crawl(title)

if __name__ == "__main__":
    main()
