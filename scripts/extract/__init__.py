# ruff: noqa: F401
from .crawler import Crawler
from .extractor import Extractor
from .gushiwen import GuShiCrawler, MingJuCrawler, ShiWenCrawler
from .wikiquote import (
    DailyDeWikiQuoteCrawler,
    DailyEnWikiQuoteCrawler,
    DailyEsWikiQuoteCrawler,
    DailyFrWikiQuoteCrawler,
    DailyJaWikiQuoteCrawler,
    DailyRuWikiQuoteCrawler,
    DeWikiQuoteCrawler,
    EnWikiQuoteCrawler,
    EsWikiQuoteCrawler,
    FrWikiQuoteCrawler,
    JaWikiQuoteCrawler,
    RuWikiQuoteCrawler,
    WikiQuoteCrawler,
    ZhWikiQuoteCrawler,
)
from .xinhua import XinhuaCrawler
