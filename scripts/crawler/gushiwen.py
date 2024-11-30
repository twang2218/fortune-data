import sys
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
from urllib.parse import urljoin

from loguru import logger

class GushiwenCrawler:
    def __init__(self):
        self.mingju_url = "https://www.gushiwen.cn/mingjus/default.aspx?page={page}&tstr={title}&astr=&cstr=&xstr="
        self.gushi_url = "https://www.gushiwen.cn/gushi/{title}.aspx"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        self.saved_links = set()
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

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
        
    def get_file_link(self, title):
        return f"{self.data_dir}/{title}.jsonl"

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
    
    def print_dot(self):
        print(".", end="", flush=True)
        sys.stdout.flush()

    def parse_mingju(self, cookie):
        """解析名句"""
        try:
            links = cookie.find_all("a")
            if links and len(links) == 2:
                content = self.get_text(links[0])
                source = self.get_text(links[1])
                content_link = urljoin(self.mingju_url, links[0]["href"])
                source_link = urljoin(self.mingju_url, links[1]["href"])
                return content, source, content_link, source_link
            else:
                return None, None, None, None
        except Exception as e:
            print(f"Error parsing cookie: {str(e)}")
            return None, None, None, None

    def save_mingju(self, title, content, source, content_link, source_link):
        """保存名句"""
        with open(self.get_file_link(title), "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "content": content,
                        "source": source,
                        "content_link": content_link,
                        "source_link": source_link,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        self.saved_links.add(content_link)

    def crawl_mingju(self, title: str, start_page=1, end_page=1):
        """爬取指定页数的名句"""
        logger.info(f"开始爬取 《{title}》")
        # 加载已保存的名句链接
        self.data_dir = "data/mingju"
        self.saved_links = set()
        file_link = self.get_file_link(title)
        if os.path.exists(file_link):
            with open(file_link, "r", encoding="utf-8") as f:
                for line in f:
                    cookie = json.loads(line)
                    self.saved_links.add(cookie["content_link"])
            logger.debug(f"已加载已保存的名句 {len(self.saved_links)} 条")
        # 爬取名句
        for page in range(start_page, end_page + 1):
            url = f"{self.mingju_url.format(title=title, page=page)}"
            soup = self.get_page(url)
            if not soup:
                continue

            # 获取当前页面所有名句链接
            cookies = soup.find_all("div", class_="cont")
            for cookie in cookies:
                content, source, content_link, source_link = self.parse_mingju(cookie)
                if not content_link or content_link in self.saved_links:
                    self.print_dot()
                    continue
                else:
                    self.save_mingju(title, content, source, content_link, source_link)
                    print(f"{content}\n -- {source}\n%")
            print()
            # 获取下一页链接
            next_page = soup.find("a", class_="amore")
            if not next_page or not next_page.has_attr("href"):
                # 如果没有下一页，结束爬取
                logger.debug(f"当前页 {page} 无下一页")
                break
        logger.info(f"爬取 《{title}》 完成, 共爬取 {len(self.saved_links)} 条名句。")

    def crawl_gushi_entry(self, url):
        """爬取诗词详情"""
        soup = self.get_page(url)
        if not soup:
            return
        # 获取诗词内容
        yuanwen = soup.find("div", id="sonsyuanwen")
        if not yuanwen:
            logger.debug(f"无法获取诗词内容 {url}")
            return None, None, None
        title = self.get_text(yuanwen.find("h1"))
        author = self.get_text(yuanwen.find("p", class_="source"))
        content = self.get_text(yuanwen.find("div", class_="contson"))
        return title, author, content
        
    def save_gushi(self, book, title, author, content, content_link):
        """保存诗词"""
        file_link = self.get_file_link(book)
        with open(file_link, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "title": title,
                        "author": author,
                        "content": content,
                        "content_link": content_link,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        self.saved_links.add(content_link)

    def crawl_gushi(self, key: str, name: str):
        """爬取指定页数的古诗"""
        logger.info(f"开始爬取 《{name}》")
        # 加载已保存的诗词链接
        self.data_dir = "data/gushi"
        self.saved_links = set()
        file_link = self.get_file_link(name)
        if os.path.exists(file_link):
            with open(file_link, "r", encoding="utf-8") as f:
                for line in f:
                    cookie = json.loads(line)
                    self.saved_links.add(cookie["content_link"])
            logger.debug(f"已加载已保存的诗词 {len(self.saved_links)} 条")
        # 爬取诗词
        url = f"{self.gushi_url.format(title=key)}"
        soup = self.get_page(url)
        if not soup:
            logger.error(f"无法获取 {url}")
            return

        # 获取列表部分
        section = soup.find("div", class_="sons")
        # 获取所有诗词链接
        links = section.find_all("a")
        for link in links:
            if not link.has_attr("href"):
                continue
            gushi_entry_link = urljoin(self.gushi_url, link["href"])
            if gushi_entry_link in self.saved_links:
                continue
            else:
                title, author, content = self.crawl_gushi_entry(gushi_entry_link)
                if title and author and content:
                    self.save_gushi(name, title, author, content, gushi_entry_link)
                    print(f"《{title}》 -- {author}\n{content}\n%")
                else:
                    self.print_dot()
                
            print()
        logger.info(f"爬取 《{name}》 完成, 共爬取 {len(self.saved_links)} 条诗词。")

    def crawl_shiwen(self, title: str):
        """爬取指定页数的古诗"""
        logger.info(f"开始爬取 《{title}》")
        # 加载已保存的诗词链接
        link = "https://www.gushiwen.cn/shiwens/default.aspx?cstr={title}"
        data_dir = "data/shiwen"
        os.makedirs(data_dir, exist_ok=True)
        saved_links = set()
        file_link = f"{data_dir}/{title}.jsonl"
        if os.path.exists(file_link):
            with open(file_link, "r", encoding="utf-8") as f:
                for line in f:
                    cookie = json.loads(line)
                    self.saved_links.add(cookie["content_link"])
            logger.debug(f"已加载已保存的诗词 {len(saved_links)} 条")
        # 爬取诗词
        url = f"{link.format(title=title)}"
        soup = self.get_page(url)
        if not soup:
            logger.error(f"无法获取 {url}")
            return

        # 获取列表部分
        section = soup.find("div", class_="typecont")
        # 获取所有诗词链接
        links = section.find_all("a")
        for link in links:
            shiwen_entry_link = urljoin(url, link["href"])
            if shiwen_entry_link in saved_links:
                self.print_dot()
                continue
            else:
                item_title, author, content = self.crawl_gushi_entry(shiwen_entry_link)
                if item_title and author and content:
                    self.save_gushi(title, item_title, author, content, shiwen_entry_link)
                    print(f"《{item_title}》 -- {author}\n{content}\n%")
                
            print()
        logger.info(f"爬取 《{title}》 完成, 共爬取 {len(self.saved_links)} 条诗词。")

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
    
    crawler = GushiwenCrawler()

    for title in mingju_titles:
        crawler.crawl_mingju(title, 1, 100)

    for (key, name) in gushi_titles:
        crawler.crawl_gushi(key, name)
    
    for title in shiwen_title:
        crawler.crawl_shiwen(title)

if __name__ == "__main__":
    main()
