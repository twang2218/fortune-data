import os
import sqlite3
from typing import Type

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, SecretStr

LANGCHAIN_DB_PATH = "data/cache/langchain.db"
set_llm_cache(SQLiteCache(database_path=LANGCHAIN_DB_PATH))


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


def get_llm_chain(
    prompt_template: ChatPromptTemplate | str,
    model_name: str = "openai:gpt-4o",
    cls: Type[BaseModel] = BaseModel,
):
    if isinstance(prompt_template, str):
        prompt_template = get_structured_prompt(prompt_template)

    llm = load_model(model_name=model_name)
    parser = PydanticOutputParser(pydantic_object=cls)
    chain = (
        prompt_template.partial(format_instructions=parser.get_format_instructions())
        | llm
        | parser
    )
    return chain


def get_structured_prompt(system: str):
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"{system}\nReturn only the JSON format result. The format should be as follows:\n"
                + "{format_instructions}",
            ),
            ("user", "{content}"),
        ]
    )


def remove_from_cache(pattern: str):
    try:
        conn = sqlite3.connect(LANGCHAIN_DB_PATH)
        c = conn.cursor()
        sql = "DELETE FROM full_llm_cache WHERE prompt LIKE ?"
        # link = requote_uri(link)
        if "\n" in pattern:
            parts = pattern.split("\n")
            parts = [part.strip() for part in parts if len(part.strip()) > 0]
            pattern = parts[0]
        pattern_encoded = pattern.encode("unicode_escape").decode("ascii")
        c.execute(sql, (f"%{pattern_encoded}%",))
        delete_count = c.rowcount
        conn.commit()
        logger.debug(
            f"Removing {delete_count} records for {pattern} from langchain cache"
        )
    except Exception as e:
        logger.error(f"Error removing {pattern} from langchain cache: {str(e)}")
    finally:
        if conn:
            conn.close()
