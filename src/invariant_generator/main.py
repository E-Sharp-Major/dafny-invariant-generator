from infrastructure.llm import OpenAIAdapter

def main() -> None:
    adapter = OpenAIAdapter(
        model="qwen2.5-coder-3b-instruct"
    )
    result = adapter.generate_invariant()
    print(result.result)