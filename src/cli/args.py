import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CliArgs:
    path: Path
    model: str
    output: Path | None = None
    base_url: str | None = None
    max_repair_iterations: int | None = None
    dafny_path: str | None = None
    timeout: float | None = None
    ttl: int | None = None


def _dfy_file(value: str) -> Path:
    path = Path(value)
    if path.suffix.lower() != ".dfy":
        raise argparse.ArgumentTypeError(f"expected a .dfy file, got '{value}'")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file not found: '{value}'")
    return path


def _non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def _int_at_least(minimum: int):
    def parse(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not an integer") from None
        if number < minimum:
            raise argparse.ArgumentTypeError(f"must be >= {minimum}, got {number}")
        return number

    return parse


def _positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a number") from None
    if number <= 0:
        raise argparse.ArgumentTypeError(f"must be > 0, got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dafny-invariant",
        description="Generate Dafny loop invariants with a local LLM (LM Studio) "
        "and check them with the Dafny verifier.",
        epilog="exit codes: 0 verified, 1 not verified, 2 usage/config error, "
        "3 infrastructure error (LM Studio / Dafny).",
    )
    parser.add_argument("path", type=_dfy_file, metavar="PROGRAM.dfy",
                        help="Dafny source file to process")
    parser.add_argument("-m", "--model", required=True, type=_non_empty, metavar="MODEL_ID",
                        help="model identifier as shown by LM Studio")
    parser.add_argument("-o", "--output", type=Path, metavar="RESULT.dfy",
                        help="where to write the result "
                        "(default: <input stem>.inv.dfy next to the input; "
                        "the input file is never overwritten)")
    parser.add_argument("--base-url", metavar="URL",
                        help="OpenAI-compatible server URL "
                        "(env: LMSTUDIO_BASE_URL, default: http://localhost:1234/v1)")
    parser.add_argument("--max-repair-iterations", type=_int_at_least(0), metavar="N",
                        help="max verifier-feedback repair rounds, 0 disables repair (default: 3)")
    parser.add_argument("--dafny-path", metavar="PATH",
                        help="Dafny executable (env: DAFNY_PATH, default: dafny)")
    parser.add_argument("--timeout", type=_positive_float, metavar="SECONDS",
                        help="timeout for one LLM request / Dafny run (default: 120)")
    parser.add_argument("--ttl", type=_int_at_least(0), metavar="SECONDS",
                        help="how long LM Studio may keep the model loaded after the "
                        "request, frees VRAM sooner (default: 300)")
    return parser


def parse_args(argv: Sequence[str] | None = None) -> CliArgs:
    """Parse ``argv`` (``sys.argv[1:]`` when None). Exits with code 2 on bad usage."""
    ns = build_parser().parse_args(argv)
    return CliArgs(
        path=ns.path,
        model=ns.model,
        output=ns.output,
        base_url=ns.base_url,
        max_repair_iterations=ns.max_repair_iterations,
        dafny_path=ns.dafny_path,
        timeout=ns.timeout,
        ttl=ns.ttl,
    )