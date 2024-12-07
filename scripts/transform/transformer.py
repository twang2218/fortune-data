from typing import List

from model import Cookie
from pydantic import BaseModel


class Transformer(BaseModel):
    @staticmethod
    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        raise NotImplementedError
