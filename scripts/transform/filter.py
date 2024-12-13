from numbers import Number
from typing import List

from common import Cookie
from pydantic import Field

from .transformer import Transformer


class FilterByLength(Transformer):
    min_length: int = Field(default=0, description="The minimum length of the content.")
    max_length: int = Field(
        default=10000, description="The maximum length of the content."
    )

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return [
            cookie
            for cookie in cookies
            if self.min_length <= len(cookie.content) <= self.max_length
        ]


class FilterByScore(Transformer):
    score: float = Field(
        default=5.0, description="The overall score threshold of the content."
    )

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return [cookie for cookie in cookies if self.score <= cookie.score.overall]


class FilterByRank(Transformer):
    top: int = Field(default=100, description="Only keep the top ranked cookies.")

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        # sort cookies by overall score
        cookies.sort(
            key=lambda cookie: cookie.score.overall
            if cookie.score and isinstance(cookie.score.overall, Number)
            else 0,
            reverse=True,
        )
        return cookies[: self.top]


class Sorter(Transformer):
    reversed: bool = Field(default=True, description="Sort in reversed order.")

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        cookies.sort(
            key=lambda cookie: cookie.score.overall
            if cookie.score and isinstance(cookie.score.overall, Number)
            else 0,
            reverse=self.reversed,
        )
        return cookies
