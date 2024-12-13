# ruff: noqa: F401
from .crawler import Crawler
from .extractor import Extractor
from .gushiwen import GuShiCrawler, MingJuCrawler, ShiWenCrawler
from .wikiquote import (
    DailyDeWikiQuoteCrawler,
    DailyEnWikiQuoteCrawler,
    DailyFrWikiQuoteCrawler,
    DailyRuWikiQuoteCrawler,
    DeWikiQuoteCrawler,
    EnWikiQuoteCrawler,
    FrWikiQuoteCrawler,
    RuWikiQuoteCrawler,
    WikiQuoteCrawler,
    ZhWikiQuoteCrawler,
)
from .xinhua import XinhuaCrawler
