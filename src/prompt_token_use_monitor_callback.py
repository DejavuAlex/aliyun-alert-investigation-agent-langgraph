import os
from typing import Any, Optional
from uuid import UUID

import tiktoken
from langchain_core.callbacks import BaseCallbackHandler

from log_config import get_logger
logger = get_logger(__name__)
"""
当发给LLM时候需要观察token使用数量，prompt内容，以优化prompt

"""
class Prompt_Token_Use_Monitor_Callback(BaseCallbackHandler):
    def __init__(self, max_tokens=int(os.getenv("LLM_MAX_TOKENS","260000")),store_stats: bool = True,):
        self.max_tokens = max_tokens
        self.store_stats = store_stats
        self.last_total: int = 0
        self.last_prompt_token_counts: list[int] = []

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
        logger.debug("=== DEBUG LLM INPUT ===")
        model_name = (serialized or {}).get("model") or (serialized or {}).get("name")
        try:
            enc = tiktoken.encoding_for_model(model_name) if model_name else tiktoken.get_encoding("cl100k_base")
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")

        prompt_token_counts = [len(enc.encode(p)) for p in prompts]
        total = sum(prompt_token_counts)

        self.last_total = total
        self.last_prompt_token_counts = prompt_token_counts if self.store_stats else []

        for i, (p, cnt) in enumerate(zip(prompts, prompt_token_counts)):
            logger.debug(f"Prompt {i} tokens={cnt} preview={p[:200]!r}......")

        logger.debug(f"Prompt token counts: {prompt_token_counts}; total={total}; max={self.max_tokens}")
        if total > self.max_tokens:
            logger.warning(f"Total prompt tokens {total} exceed max_tokens {self.max_tokens}")