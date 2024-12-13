import os
import sqlite3
from pathlib import Path
from typing import Any, List, Type

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai.chat_models import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, Field, SecretStr

langchain_cache_dir = None


class Agent(BaseModel):
    prompt: str = Field(
        default="", description="The prompt template for the language model."
    )
    cls: Type[BaseModel] = Field(default=BaseModel, description="The model class.")
    base_model: str = Field(
        default="openai:gpt-4o-mini", description="The base model name."
    )
    fallback_model: str = Field(
        default="openai:gpt-4o", description="The fallback model name."
    )
    batch_size: int = Field(
        default=50, description="The batch size for the language model invocation."
    )

    chain: Any = None

    def __init__(
        self,
        **data,
    ) -> None:
        super().__init__(**data)

    def get_prompt(self):
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt
                    + "\n"
                    + "Return only the JSON format result. The format should be as follows:"
                    + "\n"
                    + "{format_instructions}",
                ),
                ("user", "{content}"),
                MessagesPlaceholder("last_output", optional=True),
            ]
        )

    def get_chain(self):
        if not self.chain:
            # llm = load_model(model_name=self.base_model).with_fallbacks(
            #     [load_model(model_name=self.fallback_model)]
            # )
            parser = PydanticOutputParser(pydantic_object=self.cls)
            prompt_template = self.get_prompt().partial(
                format_instructions=parser.get_format_instructions()
            )
            model_base = load_model(model_name=self.base_model)
            model_fallback = load_model(model_name=self.fallback_model)

            self.chain = (prompt_template | model_base | parser).with_fallbacks(
                [
                    (
                        # retry once more with the base model
                        self.exception_to_messages
                        | prompt_template
                        | model_base
                        | parser
                    ),
                    (
                        # retry once more with the fallback model
                        self.chain_logger | prompt_template | model_fallback | parser
                    ),
                ],
                exception_key="exception",
            )
        return self.chain

    def exception_to_messages(self, inputs: dict) -> dict:
        logger.warning(
            f"Agent({self.base_model}) error: {inputs['exception']} for input: {inputs['content']}"
        )
        if "DataInspectionFailed" in str(inputs["exception"]):
            # should not retried for certain errors
            raise inputs["exception"]
        else:
            # remove llm call cache for the failed call
            Agent.remove_from_cache(inputs["content"])
        # Add historical messages to the original input, so the model knows that it made a mistake with the last tool call.
        messages = [
            AIMessage(content=str(inputs.pop("exception"))),
            HumanMessage(
                content="The last call raised an exception. Try calling again with corrected arguments. Do not repeat mistakes."
            ),
        ]
        inputs["last_output"] = messages
        return inputs

    def chain_logger(self, inputs: dict) -> dict:
        logger.debug(f"Try fallback model ({self.fallback_model})")
        return inputs

    def process(self, contents: List[str]) -> List:
        inputs = [{"content": content} for content in contents]
        results = []
        # process the inputs
        # logger.debug(f"Agent.process(): {len(inputs)} contents")
        for i in range(0, len(inputs), self.batch_size):
            batch_inputs = inputs[i : i + self.batch_size]
            batch_results = self.get_chain().batch(batch_inputs, return_exceptions=True)
            print("." * len(batch_results), end="", flush=True)
            results.extend(batch_results)
        # return the results
        return results

    @staticmethod
    def init_cache(cache_dir: str = None):
        global langchain_cache_dir
        if not cache_dir:
            langchain_cache_dir = str(
                Path(__file__).parent.parent / ".cache" / "langchain.db"
            )
        else:
            langchain_cache_dir = str(Path(cache_dir) / "langchain.db")
        logger.debug(f"Langchain cache: {langchain_cache_dir}")
        set_llm_cache(SQLiteCache(database_path=langchain_cache_dir))

    @staticmethod
    def remove_from_cache(pattern: str):
        global langchain_cache_dir
        with sqlite3.connect(langchain_cache_dir) as conn:
            try:
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
                    f"Removed {delete_count} records for {pattern} from langchain cache"
                )
            except Exception as e:
                logger.error(f"Error removing {pattern} from langchain cache: {str(e)}")
                conn.rollback()


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
