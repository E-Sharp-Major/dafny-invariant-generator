from openai import OpenAI

from domain import GenerateInvariantResult

from .llm_adapter import LLMAdapter

class OpenAIAdapter(LLMAdapter):
    def __init__(self, base_url: str = "http://localhost:1234/v1",
        api_key: str = "lm-studio",
        model: str = "local-model",) -> None:
        super().__init__()

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model

    def generate_invariant(self) -> GenerateInvariantResult:
        response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": """
                You are an expert in Dafny and formal verification.

                Your task is to generate loop invariants for the provided Dafny code.

                Requirements:
                - Generate only loop invariants.
                - Do not modify the original code.
                - Do not generate preconditions, postconditions, ghost functions, lemmas, or assertions.
                - Each invariant must be valid Dafny syntax and type-correct.
                - Invariants must hold before the first loop iteration.
                - Invariants must be preserved after every loop iteration.
                - Invariants must be strong enough to help prove the method's postconditions.
                - Do not introduce unnecessary or redundant invariants.
                - Do not use operations between incompatible types.
                - Use quantified expressions when they clearly express properties of processed array or sequence elements.
                - Return only the generated invariant clauses.
                - Do not include explanations or Markdown code blocks.
                """,
            },
            {
                "role": "user",
                "content": """
            Generate loop invariants for the following Dafny method.

            Consider all loops in the method.

            BEGIN DAFNY
            method findMin(a: array<int>) returns (res: int)
            requires a.Length >= 1
            ensures forall k :: 0 <= k < a.Length ==> res <= a[k]
            {
                var min: int := a[0];
                var i := 0;
                while i < a.Length
                {
                    if min > a[i]
                    {
                        min := a[i];
                    }
                    i := i + 1;
                }
                return min;
            }
            END DAFNY
                """,
            },
        ],
        temperature=0.2,
        )

        content = response.choices[0].message.content

        if content is None:
            raise RuntimeError("The model returned an empty response.")

        return GenerateInvariantResult(content)

    def repair_invariant(self) -> None:
        raise NotImplementedError()