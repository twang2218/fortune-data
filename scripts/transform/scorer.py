from typing import List

from common import Agent, Cookie, Score
from pydantic import Field

from .transformer import Transformer


class Scorer(Transformer):
    model_name: str = Field(
        default="openai:gpt-4o-mini",
        description="The language model provider. format: 'provider:model_name', e.g. 'openai:gpt-4o'",
    )
    model_name_fallback: str = Field(
        default="openai:gpt-4o",
        description="The fallback language model provider. format: 'provider:model_name', e.g. 'openai:gpt-4o'",
    )
    prompt: str = Field(
        default="Please evaluate the following content across multiple dimensions, and provide a score for each dimension. note: please use the same language of 'content' to explain.",
        description="The prompt for the language model.",
    )
    batch_size: int = Field(
        default=10, description="The batch size for processing the content."
    )

    def score(self, cookies: List[Cookie]) -> List[Cookie]:
        agent = Agent(
            prompt=self.prompt,
            base_model=self.model_name,
            fallback_model=self.model_name_fallback,
            cls=Cookie,
            batch_size=self.batch_size,
        )

        results = agent.process([cookie.model_dump_json() for cookie in cookies])

        for i, result in enumerate(results):
            if result and result.score:
                result.score.update_overall()
                cookies[i].score = result.score
            else:
                cookies[i].score = Score()
        return cookies

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return self.score(cookies)
