import os
from collections.abc import Sequence

import openai
from openai import OpenAI

from application.ports import LLMClient, ModelCatalog
from domain import (
    GenParams,
    LLMUnavailableError,
    Message,
    ModelNotFoundError,
    ProviderConfig,
)

from .lmstudio_catalog import LMStudioCatalog

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_API_KEY = "lm-studio"  # LM Studio ignores the key, the OpenAI SDK requires one


class LMStudioClient(LLMClient, name="lmstudio"):
    """LM Studio through its OpenAI-compatible chat API.

    LM Studio specifics live here and nowhere else: the ``ttl`` field that
    limits how long a JIT-loaded model stays in VRAM, and the model catalog
    """

    def __init__(self, base_url: str, api_key: str, timeout: float) -> None:
        self._base_url = base_url
        self._timeout = timeout
        # No SDK retries: against a local server a failure should surface at once.
        self._client = OpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0
        )

    @classmethod
    def from_config(cls, cfg: ProviderConfig) -> "LMStudioClient":
        return cls(
            base_url=cfg.base_url or os.environ.get("LMSTUDIO_BASE_URL") or DEFAULT_BASE_URL,
            api_key=os.environ.get("LMSTUDIO_API_KEY") or DEFAULT_API_KEY,
            timeout=cfg.timeout,
        )

    def complete(self, messages: Sequence[Message], params: GenParams) -> str:
        request: dict = {
            "model": params.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": params.temperature,
        }
        if params.max_tokens is not None:
            request["max_tokens"] = params.max_tokens
        if params.ttl is not None:
            request["extra_body"] = {"ttl": params.ttl}  # LM Studio idle TTL, seconds

        try:
            response = self._client.chat.completions.create(**request)
        except openai.NotFoundError as exc:
            raise ModelNotFoundError(
                f"LM Studio does not know the model '{params.model}'"
            ) from exc
        except openai.APIConnectionError as exc:  # includes timeouts
            raise LLMUnavailableError(
                f"cannot reach LM Studio at {self._base_url} "
                f"(is the local server running?): {exc}"
            ) from exc
        except openai.APIStatusError as exc:
            raise LLMUnavailableError(
                f"LM Studio returned HTTP {exc.status_code}: {exc.message}"
            ) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            raise LLMUnavailableError("the model returned an empty response")
        return content

    def catalog(self) -> ModelCatalog:
        return LMStudioCatalog(self._base_url, self._timeout)
