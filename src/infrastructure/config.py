import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from domain import ConfigError, GenParams
from domain.models import ProviderConfig

DEFAULT_PROVIDER = "lmstudio"
DEFAULT_DAFNY_PATH = "dafny"
DEFAULT_MAX_REPAIR_ITERATIONS = 3
DEFAULT_TIMEOUT = 120.0
DEFAULT_TTL = 300
DEFAULT_TEMPERATURE = 0.2



@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Per-model settings"""

    id: str
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int | None = None
    ttl: int | None = DEFAULT_TTL

    def to_gen_params(self) -> GenParams:
        return GenParams(
            model=self.id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            ttl=self.ttl,
        )


@dataclass(frozen=True, slots=True)
class Settings:
    input_path: Path
    output_path: Path
    model: ModelProfile
    provider: str = DEFAULT_PROVIDER
    provider_config: ProviderConfig = ProviderConfig()
    dafny_path: str = DEFAULT_DAFNY_PATH
    max_repair_iterations: int = DEFAULT_MAX_REPAIR_ITERATIONS
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def resolve(
        cls,
        *,
        path: Path,
        model: str,
        output: Path | None = None,
        provider: str | None = None,
        provider_options: Mapping[str, str] | None = None,
        base_url: str | None = None,
        max_repair_iterations: int | None = None,
        dafny_path: str | None = None,
        timeout: float | None = None,
        ttl: int | None = None,
        env: Mapping[str, str] | None = None,
    ) -> "Settings":
        env = os.environ if env is None else env

        output_path = output if output is not None else path.with_name(f"{path.stem}.inv.dfy")
        if output_path.resolve() == path.resolve():
            raise ConfigError("output path must differ from the input path; "
                              "the original program is never overwritten")

        resolved_timeout = DEFAULT_TIMEOUT if timeout is None else timeout
        return cls(
            input_path=path,
            output_path=output_path,
            model=ModelProfile(id=model, ttl=DEFAULT_TTL if ttl is None else ttl),
            provider=provider or env.get("DAFNY_INVARIANT_PROVIDER") or DEFAULT_PROVIDER,
            provider_config=ProviderConfig(
                base_url=base_url,
                timeout=resolved_timeout,
                options=dict(provider_options or {}),
            ),
            dafny_path=dafny_path or env.get("DAFNY_PATH") or DEFAULT_DAFNY_PATH,
            max_repair_iterations=(DEFAULT_MAX_REPAIR_ITERATIONS
                                   if max_repair_iterations is None else max_repair_iterations),
            timeout=resolved_timeout,
        )
