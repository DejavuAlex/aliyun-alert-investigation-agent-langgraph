import os
from typing import Any, Optional
from uuid import UUID

import tiktoken
from langchain_core.callbacks import BaseCallbackHandler

"""
当发给LLM时候需要观察token使用数量，prompt内容，以优化prompt

"""
class Prompt_Token_Use_Monitor_Callback(BaseCallbackHandler):
    def __init__(self, max_tokens=int(os.getenv("LLM_MAX_TOKENS","260000"))):
        self.max_tokens = max_tokens

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
         print("=== DEBUG LLM INPUT ===")
         # for p in prompts:
         #     print("get the prompt is: " + p[:300] + "...")
         enc = tiktoken.get_encoding("cl100k_base")
         total = sum(len(enc.encode(p)) for p in prompts)
         print(f"Total prompt tokens: {total}, the max tokens is {self.max_tokens}")