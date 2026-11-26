from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from domain import GenParams, Message, ModelInfo, ProviderConfig
from domain.models import VerificationResult


class ModelCatalog(ABC):
    """Optional capability: ask the server which models exist and which are loaded."""

    @abstractmethod
    def list_models(self) -> list[ModelInfo]: ...


class LLMClient(ABC):
    """Base class every LLM provider implements.

    Declaring ``class MyClient(LLMClient, name="my-provider")`` registers the
    class under that name. Classes without ``name`` (intermediate bases) are
    not registered
    """

    name: ClassVar[str]
    _registry: ClassVar[dict[str, type["LLMClient"]]] = {}

    def __init_subclass__(cls, *, name: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if name is None:
            return
        if name in LLMClient._registry:
            raise ValueError(
                f"LLM provider name '{name}' is already registered by "
                f"{LLMClient._registry[name].__module__}.{LLMClient._registry[name].__qualname__}"
            )
        cls.name = name
        LLMClient._registry[name] = cls

    @classmethod
    def providers(cls) -> dict[str, type["LLMClient"]]:
        """Snapshot of registered providers (name -> class)"""
        return dict(LLMClient._registry)

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: ProviderConfig) -> "LLMClient":
        """Build an instance from generic configuration"""

    @abstractmethod
    def complete(self, messages: Sequence[Message], params: GenParams) -> str:
        """Send a chat request and return the reply text

        Must raise ``LLMUnavailableError`` / ``ModelNotFoundError`` (never a
        vendor-specific exception) and must not return an empty string
        """

    def catalog(self) -> ModelCatalog | None:
        """Model catalog if the provider has one; None otherwise (preflight is skipped)"""
        return None

class Verifier(ABC):
    @abstractmethod
    def verify(self, source: str) -> VerificationResult:
        """Check a Dafny program.
        
        A program that does not verify, including syntax errors and timeouts, is
        a normal result: ok is False and errors holds one entry per diagnostic,
        with locations relative to ``source``. Raises ``InfrastructureError``
        only when the verifier itself cannot run, e.g. ``DafnyNotFoundError``
        """
