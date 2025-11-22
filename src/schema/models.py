from enum import StrEnum, auto
from typing import TypeAlias


class Provider(StrEnum):
    OPENAI = auto()



class OpenAIModelName(StrEnum):
    GPT_5 = "gpt-5-2025-08-07"


AllModelEnum: TypeAlias = (
    OpenAIModelName
)

AVAILABLE_MODELS:set[AllModelEnum] = {
    OpenAIModelName.GPT_5
}

DEFAULT_MODEL = OpenAIModelName.GPT_5
