from langchain_core.callbacks import StdOutCallbackHandler

from langchain_openai import ChatOpenAI
from pydantic import SecretStr, Field

from src.logging_callback_handler import LoggingCallbackHandler
from src.prompt_token_use_monitor_callback import Prompt_Token_Use_Monitor_Callback
import os
from src.env_config import set_env
set_env()
llm = ChatOpenAI(
    temperature=0,
    model=os.getenv("LLM_MODEL", "gpt-5-2025-08-07"),
    api_key=SecretStr(os.getenv("LLM_API_KEY")),
    # api_key=SecretStr("Xw7VKR+e+ozUxbNbvnQxhsGYK2Jt"),
    base_url=os.getenv("LLM_BASE_URL"),
    callbacks=[Prompt_Token_Use_Monitor_Callback(),LoggingCallbackHandler()]
)