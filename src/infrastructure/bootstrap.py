from adapters.dafny.dafny_cli_verifier import DafnyCliVerifier
from adapters.llm import discover_providers
from application.ports import LLMClient, Verifier
from domain import ConfigError
from infrastructure.config import Settings


def build_llm_client(settings: Settings) -> LLMClient:
    """Pick the provider by name from the auto-discovered set"""
    providers = discover_providers()
    try:
        provider = providers[settings.provider]
    except KeyError:
        raise ConfigError(
            f"unknown provider '{settings.provider}'; "
            f"available: {', '.join(sorted(providers))}"
        ) from None
    return provider.from_config(settings.provider_config)

def build_verifier(settings: Settings) -> Verifier:
    return DafnyCliVerifier(settings.dafny_path, settings.timeout)

