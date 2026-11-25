import importlib
import pkgutil
import warnings
from importlib.metadata import entry_points

from application.ports import LLMClient

ENTRY_POINT_GROUP = "dafny_invariant.llm"

def discover_providers() -> dict[str, type[LLMClient]]:
    for module in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{module.name}")

    for entry_point in entry_points(group=ENTRY_POINT_GROUP):
        try:
            entry_point.load()
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"skipping LLM plugin '{entry_point.name}': {exc}", stacklevel=2)

    return LLMClient.providers()