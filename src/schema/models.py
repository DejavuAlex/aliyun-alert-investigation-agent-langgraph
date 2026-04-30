from enum import StrEnum, auto
from typing import TypeAlias

class Provider(StrEnum):
    OPENAI = auto()
    DASHSCOPE = auto()

class OpenAIModelName(StrEnum):
    GPT_5 = "gpt-5-2025-08-07"

class DashScopeModelName(StrEnum):
    QWEN3_MAX = "qwen3-max"
    QWEN_MAX = "qwen-max"
    QWEN_PLUS = "qwen-plus"
    QWEN_TURBO = "qwen-turbo"

AllModelEnum: TypeAlias = (
    OpenAIModelName | DashScopeModelName
)

AVAILABLE_MODELS:set[AllModelEnum] = {
    OpenAIModelName.GPT_5,
    DashScopeModelName.QWEN3_MAX,
    DashScopeModelName.QWEN_MAX,
    DashScopeModelName.QWEN_PLUS,
    DashScopeModelName.QWEN_TURBO,
}

DEFAULT_MODEL = DashScopeModelName.QWEN3_MAX
