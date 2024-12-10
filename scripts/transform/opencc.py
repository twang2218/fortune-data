from typing import Any, List

from opencc import OpenCC
from pydantic import Field

from common import Cookie

from .transformer import Transformer


class ChineseConverter(Transformer):
    lang: str = Field(default="", description="The language to convert to.")
    config: str = Field(default="", description="The configuration for OpenCC.")
    converter: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.config:
            match self.lang:
                case "zh_CN":
                    self.config = "t2s"
                case "zh_TW":
                    self.config = "s2tw"
                case "zh_HK":
                    self.config = "s2hk"
                case "zh_SG":
                    self.config = "t2s"
                case _:
                    self.config = "t2s"
        self.converter = OpenCC(self.config)

    def convert(self, text):
        return self.converter.convert(text)

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        for cookie in cookies:
            cookie.content = self.convert(cookie.content)
            cookie.source = self.convert(cookie.source)
            cookie.title = self.convert(cookie.title)
            cookie.author = self.convert(cookie.author)

        return cookies
