from typing import List
from pydantic import BaseModel

from model import Cookie, CookieJar
from .crawler import Crawler


class Extractor(BaseModel):
    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        match jar.extractor.split("."):
            case "crawler", _, _, _:
                return Crawler.extract(jar)
            case _:
                raise NotImplementedError
