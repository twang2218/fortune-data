from typing import List

from common import Cookie
from pydantic import BaseModel


class Transformer(BaseModel):
    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        raise NotImplementedError
