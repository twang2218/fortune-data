from typing import Any, List, Type

from loguru import logger
from model import Cookie, Score
from pydantic import BaseModel, Field
from utils import get_llm_chain, get_structured_prompt, remove_from_cache

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
    chain: Any = None
    chain_fallback: Any = None

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"Create chain => model: {self.model_name}")
        self.chain = self.get_chain(self.model_name)
        logger.debug(f"Create fallback chain => model: {self.model_name_fallback}")
        self.chain_fallback = self.get_chain(self.model_name_fallback)

    def get_chain(
        self, model_name: str = "openai:gpt-4o", cls: Type[BaseModel] = Cookie
    ):
        prompt_template = get_structured_prompt(self.prompt)
        return get_llm_chain(
            prompt_template=prompt_template, model_name=model_name, cls=Cookie
        )

    def score(self, cookies: List[Cookie]) -> List[Cookie]:
        for i in range(0, len(cookies), self.batch_size):
            # logger.debug(f"Processing batch {i} to {i+self.batch_size} of {len(cookies)}")
            batch_cookies = cookies[i : i + self.batch_size]
            batch_inputs = [
                {"content": cookie.model_dump_json()} for cookie in batch_cookies
            ]
            # Run normal chain
            results = self.chain.batch(batch_inputs, return_exceptions=True)
            for j, result in enumerate(results):
                # had exception or didn't generate a score
                if isinstance(result, Exception) or not result.score:
                    logger.warning(
                        f"Failed to score the cookie on chain '{self.model_name}': cookie: {batch_cookies[j].model_dump_json()} => {result}"
                    )
                    err_msg = str(result) if isinstance(result, Exception) else ""
                    if "DataInspectionFailed" not in err_msg:
                        remove_from_cache(batch_cookies[j].content)
                    # fallback
                    try:
                        # fallback to chain_fallback
                        result = self.chain_fallback.invoke(batch_inputs[j])
                        logger.debug(
                            f"fallback chain '{self.model_name_fallback}' result: {result.score.model_dump_json()}"
                        )
                    except Exception as e:
                        # cannot fallback, set score to 0
                        logger.error(
                            f"Failed on fallback chain '{self.model_name_fallback}': {e}"
                        )
                        remove_from_cache(batch_cookies[j].content)
                        result = Cookie()
                        result.score = Score()

                if result and result.score:
                    result.score.update_overall()
                    cookies[i + j].score = result.score
                    print(".", end="", flush=True)
                    # logger.debug(f"cookie: {batch_cookies[j]} => {result.score.model_dump_json()}")
                else:
                    logger.warning(
                        f"Fail to have a score for cookie: {batch_cookies[j]} => {result.model_dump_json()}"
                    )
        return cookies

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return self.score(cookies)
