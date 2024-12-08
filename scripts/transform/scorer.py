import os
import sqlite3
from typing import List

from langchain.globals import set_llm_cache, get_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from loguru import logger
from model import Cookie, CookieList
from pydantic import Field, SecretStr

from .transformer import Transformer

LANGCHAIN_DB_PATH = "data/cache/langchain.db"
set_llm_cache(SQLiteCache(database_path=LANGCHAIN_DB_PATH))


class Scorer(Transformer):
    provider: str = Field(default="openai", description="The language model provider.")
    model_name: str = Field(
        default="gpt-4o-mini", description="The language model name."
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

    def score_batch(self, cookies: List[Cookie]) -> List[Cookie]:
        # Construct the chain
        m = load_model(provider=self.provider, model_name=self.model_name)
        parser = PydanticOutputParser(pydantic_object=CookieList)
        chain = (
            self.prompt_template.partial(
                format_instructions=parser.get_format_instructions()
            )
            | m
            | parser
        )

        cookie_list = CookieList(cookies=cookies)
        results = chain.invoke({"content": cookie_list.model_dump_json()})
        if not results:
            raise ValueError(
                f"Failed to score batch: [{len(cookies)}]: {cookies[0].model_dump_json()}"
            )
        else:
            for cookie in results.cookies:
                # TODO: check if this can update the cookie in the original list
                cookie.score.update_overall()
        return results

    def score_single(self, cookie: Cookie) -> Cookie:
        # Construct the chain
        m = load_model(provider=self.provider, model_name=self.model_name)
        parser = PydanticOutputParser(pydantic_object=Cookie)
        chain = (
            self.prompt_template.partial(
                format_instructions=parser.get_format_instructions()
            )
            | m
            | parser
        )

        try:
            result = chain.invoke({"content": cookie.model_dump_json()})
            if not result:
                raise ValueError("result is None")
            else:
                result.score.update_overall()
            return result
        except Exception as e:
            remove_link_from_cache(cookie.link)
            raise e
    def score(self, cookies: List[Cookie]) -> List[Cookie]:
        logger.info(
            f"LLM Model for scoring: [{self.provider}:{self.model_name}], batch_size: {self.batch_size}, cookies: {len(cookies)}"
        )
        if self.batch_size == 1:
            for i, cookie in enumerate(cookies):
                try:
                    cookie.score = self.score_single(cookie).score
                    print(".", end="", flush=True)
                    # if (i + 1) % 50 == 0:
                    #     print()
                except Exception as e:
                    logger.error(
                        f"Failed to score cookie: {cookie.model_dump_json()}: {e}"
                    )
        else:
            for i in range(0, len(cookies), self.batch_size):
                logger.debug(
                    f"Processing batch {i} to {i+self.batch_size} of {len(cookies)}"
                )
                batch_cookies = cookies[i : i + self.batch_size]
                try:
                    batch_results = self.score_batch(batch_cookies)
                    for j, cookie in enumerate(batch_results.cookies):
                        cookies[i + j].score = cookie.score
                        print(".", end="", flush=True)
                    # print("." * self.batch_size)
                except Exception as e:
                    logger.error(
                        f"Failed to score batch {i} to {i+self.batch_size}: {e}"
                    )
                    continue

        return cookies

    def transform(self, cookies: List[Cookie]) -> List[Cookie]:
        return self.score(cookies)


def load_model(
    provider: str = "openai", model_name: str = "gpt-4o-mini"
) -> BaseChatModel:
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

def remove_link_from_cache(link:str):
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
