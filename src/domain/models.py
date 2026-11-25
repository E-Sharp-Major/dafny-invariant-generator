from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class Message:
    """One chat message sent to the LLM"""

    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class GenParams:
    """Generation parameters for a single LLM request"""

    model: str
    temperature: float = 0.2
    max_tokens: int | None = None
    ttl: int | None = None


@dataclass(frozen=True, slots=True)
class GenerateInvariantResult:
    """Raw invariant text produced by the model"""

    result: str


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of one Dafny verification run"""

    ok: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """A model known to the LLM server and whether it currently occupies memory"""

    id: str
    loaded: bool

@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Generic provider configuration. Each provider takes what it needs.

    ``base_url`` None means "the provider's own default". Anything
    provider-specific goes into ``options`` (``--provider-option key=value``),
    so ``Settings`` never grows a field for a single provider. Secrets (API
    keys) are not passed here; a provider reads them from its own env variable.
    """

    base_url: str | None = None
    timeout: float = 120.0
    options: Mapping[str, str] = field(default_factory=dict)