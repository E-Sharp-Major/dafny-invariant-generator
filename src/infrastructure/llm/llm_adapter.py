from abc import ABC, abstractmethod

from domain import GenerateInvariantResult

class LLMAdapter(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def generate_invariant(self) -> GenerateInvariantResult:
        ...

    @abstractmethod
    def repair_invariant(self) -> None:
        ...