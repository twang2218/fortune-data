import os
import sqlite3
from typing import Any, List, Type

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from loguru import logger
from model import Cookie, Score
from pydantic import BaseModel, Field, SecretStr

from .transformer import Transformer

LANGCHAIN_DB_PATH = "data/cache/langchain.db"
set_llm_cache(SQLiteCache(database_path=LANGCHAIN_DB_PATH))


class Scorer(Transformer):
    model_name: str = Field(
        default="openai:gpt-4o-mini",
        description="The language model provider. format: 'provider:model_name', e.g. 'openai:gpt-4o'",
    )
    model_name_fallback: str = Field(
        default="openai:gpt-4o",
        description="The fallback language model provider. format: 'provider:model_name', e.g. 'openai:gpt-4o'",
    )
    prompt_template: ChatPromptTemplate = Field(
        default=ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
        Please evaluate the following content across multiple dimensions, and provide a score for each dimension.
        note: please use the same language of 'content' to explain.
        Return only the JSON format result. The format should be as follows:
        {format_instructions}
        """,
                ),
                ("user", "{content}"),
            ]
        ),
        description="The prompt template for the language model.",
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
        llm = load_model(model_name=model_name)
        parser = PydanticOutputParser(pydantic_object=cls)
        chain = (
            self.prompt_template.partial(
                format_instructions=parser.get_format_instructions()
            )
            | llm
            | parser
        )
        return chain

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
                if isinstance(result, Exception):
                    logger.warning(
                        f"Failed to score the cookie on chain '{self.model_name}': cookie: {batch_cookies[j].model_dump_json()} => {result}"
                    )
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
                        result = Cookie()
                        result.score = Score()

                if result:
                    result.score.update_overall()
                    cookies[i + j].score = result.score
                    print(".", end="", flush=True)
                    # logger.debug(f"cookie: {batch_cookies[j]} => {result.score.model_dump_json()}")
        return cookies

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return self.score(cookies)


def load_model(model_name: str = "openai:gpt-4o") -> BaseChatModel:
    provider, model_name = model_name.split(":")
    # logger.info(f"model: {provider} : {model_name}")
    m: BaseChatModel
    if provider == "openai":
        # extra_kwargs = self.__get_extra_kwargs()
        # model_name = "gpt-4o-mini"
        m = ChatOpenAI(model=model_name)
    elif provider == "tongyi":
        import dashscope  # type: ignore # noqa: F401

        # model_name = "qwen-plus"
        m = ChatTongyi(model=model_name, api_key=None)
    elif provider == "moonshot":
        m = ChatOpenAI(
            model=model_name,
            api_key=SecretStr(os.environ.get("MOONSHOT_API_KEY") or ""),
            base_url="https://api.moonshot.cn/v1",
        )
        # https://github.com/langchain-ai/langchain/issues/27058
        # m = MoonshotChat(model=model_name)
    elif provider == "deepseek":
        m = ChatOpenAI(
            model=model_name,
            api_key=SecretStr(os.environ.get("DEEPSEEK_API_KEY") or ""),
            base_url="https://api.deepseek.com",
        )
    # elif provider == "anthropic":
    #     m = ChatAnthropic(model_name=model_name, timeout=60, stop=None)
    return m


def remove_link_from_cache(link: str):
    try:
        conn = sqlite3.connect(LANGCHAIN_DB_PATH)
        c = conn.cursor()
        sql = "DELETE FROM full_llm_cache WHERE prompt LIKE ?"
        c.execute(sql, (f"%{link}%",))
        delete_count = c.rowcount
        conn.commit()
        logger.debug(f"Removing {delete_count} records for {link} from langchain cache")
    except Exception as e:
        logger.error(f"Error removing {link} from langchain cache: {str(e)}")
    finally:
        if conn:
            conn.close()
