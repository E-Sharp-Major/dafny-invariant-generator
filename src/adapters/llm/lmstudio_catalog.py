import json
import urllib.error
import urllib.request

from application.ports import ModelCatalog
from domain import LLMUnavailableError, ModelInfo

_TEXT_MODEL_TYPES = {"llm", "vlm"}


class LMStudioCatalog(ModelCatalog):
    """Lists models through LM Studio's REST API: ``GET /api/v1/models``.

    The endpoint returns every downloaded model with a ``state`` of ``loaded``
    or ``not-loaded``. This is read-only: it never loads or unloads anything.
    """

    def __init__(self, base_url: str, timeout: float) -> None:
        # The OpenAI-compatible URL ends in /v1; the REST API lives at the server root.
        root = base_url.rstrip("/")
        root = root.removesuffix("/v1")
        self._url = f"{root}/api/v1/models"
        self._timeout = timeout

    def list_models(self) -> list[ModelInfo]:
        try:
            with urllib.request.urlopen(self._url, timeout=self._timeout) as response:
                payload = json.load(response)
            entries = payload["data"]
        except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError) as exc:
            raise LLMUnavailableError(f"cannot list models from {self._url}: {exc}") from exc

        return [
            ModelInfo(id=entry["id"], loaded=entry.get("state") == "loaded")
            for entry in entries
            # Embedding models are not chat models; keep entries with no "type" field.
            if entry.get("type", "llm") in _TEXT_MODEL_TYPES
        ]
