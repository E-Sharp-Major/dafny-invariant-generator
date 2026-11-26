import sys
from dataclasses import asdict

from cli.args import parse_args
from domain import ConfigError, InfrastructureError, Message
from infrastructure.bootstrap import build_llm_client
from infrastructure.config import Settings

SYSTEM_PROMPT = """You are an expert in Dafny and formal verification.

Your task is to generate loop invariants for the provided Dafny code.

Requirements:
- Generate only loop invariants
- Do not modify the original code
- Do not generate preconditions, postconditions, ghost functions, lemmas, or assertions
- Each invariant must be valid Dafny syntax and type-correct
- Invariants must hold before the first loop iteration
- Invariants must be preserved after every loop iteration
- Invariants must be strong enough to help prove the method's postconditions
- Do not introduce unnecessary or redundant invariants
- Use quantified expressions when they clearly express properties of processed array or sequence elements
- Return code with generated invariants included
- Do not include explanations or Markdown code blocks"""

USER_PROMPT = """Generate loop invariants for the following Dafny method.

Consider all loops in the method.

BEGIN DAFNY
{source}
END DAFNY"""


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        settings = Settings.resolve(**asdict(args))
        llm_client = build_llm_client(settings)

        try:
            source = settings.input_path.read_text(encoding="utf-8")
        except OSError as e:
            raise InfrastructureError(f"cannot read {settings.input_path}: {e}") from e

        messages = [
            Message("system", SYSTEM_PROMPT),
            Message("user", USER_PROMPT.format(source=source)),
        ]
        print(llm_client.complete(messages, settings.model.to_gen_params()))
        return 0
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except InfrastructureError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3