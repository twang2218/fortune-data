from typing import List

from pydantic import BaseModel

from common import Cookie


class Transformer(BaseModel):
    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        raise NotImplementedError
