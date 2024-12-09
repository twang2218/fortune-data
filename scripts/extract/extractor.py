from typing import List
from pydantic import BaseModel

from model import Cookie, CookieJar
from .crawler import Crawler


class Extractor(BaseModel):
    @staticmethod
    def extract(jar: CookieJar) -> List[Cookie]:
        parts = jar.extractor.split(".")
        match parts[0]:
            case "crawler":
                return Crawler.extract(jar)
            case _:
                raise NotImplementedError
