from typing import TypeAlias

from langchain_core.callbacks import StdOutCallbackHandler

from langchain_openai import ChatOpenAI
from pydantic import SecretStr, Field

from schema.models import AllModelEnum, OpenAIModelName
from logging_callback_handler import LoggingCallbackHandler
from prompt_token_use_monitor_callback import Prompt_Token_Use_Monitor_Callback
import os
from env_config import set_env
set_env()

ModelT: TypeAlias = (
    ChatOpenAI
)


llm = ChatOpenAI(
    temperature=0,
    model=os.getenv("LLM_MODEL", "gpt-5-2025-08-07"),
    api_key=SecretStr(os.getenv("LLM_API_KEY")),
    base_url=os.getenv("LLM_BASE_URL"),
    timeout=120.0,
    max_retries=3,
    callbacks=[Prompt_Token_Use_Monitor_Callback(),LoggingCallbackHandler()]
)

def get_model(model_name:AllModelEnum) -> ModelT:
    if model_name in OpenAIModelName:
        return llm
    else:
        raise RuntimeError(f"Model {model_name} is not supported")