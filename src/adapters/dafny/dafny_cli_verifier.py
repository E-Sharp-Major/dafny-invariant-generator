import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path

from application.ports import Verifier
from domain import DafnyNotFoundError, VerificationResult

_HEADER = re.compile(
    r"^(?P<path>.+?)\((?P<line>\d+),(?P<col>\d+)\): "
    r"(?P<kind>Error|Related location|Warning)(?P<rest>.*)$"
)
_SUMMARY = re.compile(r"finished with (?P<verified>\d+) verified, (?P<errors>\d+) errors?")
_NOISE = re.compile(
    r"^(Prover error:|Dafny program verifier finished|\d+ (parse|resolution/type) errors? detected)"
)
_FALLBACK_LINES = 15


class DafnyCliVerifier(Verifier):
    def __init__(self, dafny_path: str, timeout: float) -> None:
        self._dafny_path = dafny_path
        self._timeout = timeout

    def verify(self, source: str) -> VerificationResult:
        # A fresh ASCII path avoids console encoding damage and long synced-folder paths
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / "program.dfy"
            program.write_text(source, encoding="utf-8")
            output, returncode = self._run(program)

        if output is None:
            return VerificationResult(
                ok=False,
                errors=(f"verification timed out after {self._timeout:g} seconds",),
            )

        blocks = _error_blocks(output)
        summary = _SUMMARY.search(output)
        ok = returncode == 0 and summary is not None and summary["errors"] == "0" and not blocks
        if ok:
            return VerificationResult(ok=True)
        if blocks:
            return VerificationResult(ok=False, errors=tuple(blocks))
        return VerificationResult(ok=False, errors=(_tail(output),))

    def _run(self, program: Path) -> tuple[str | None, int]:
        command = [self._dafny_path, "verify", str(program)]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=os.name != "nt",
            )
        except OSError as exc:
            raise DafnyNotFoundError(f"cannot start Dafny at '{self._dafny_path}': {exc}") from exc

        try:
            output, _ = process.communicate(timeout=self._timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(process)
            process.communicate()
            return None, -1
        return output, process.returncode


def _kill_tree(process: subprocess.Popen) -> None:
    # Dafny starts Z3 as a child; killing only Dafny would leave Z3 consuming CPU
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False
        )
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass


def _error_blocks(output: str) -> list[str]:
    blocks: list[list[str]] = []
    in_block = False
    for line in output.splitlines():
        if not line.strip() or _NOISE.match(line):
            continue
        header = _HEADER.match(line)
        if header is None:
            if in_block:
                blocks[-1].append(line.rstrip())
            continue
        text = (
            f"program.dfy({header['line']},{header['col']}): "
            f"{header['kind']}{header['rest']}"
        )
        if header["kind"] == "Error":
            blocks.append([text])
            in_block = True
        elif header["kind"] == "Related location" and in_block:
            blocks[-1].append(text)
        else:
            in_block = False
    return ["\n".join(block) for block in blocks]


def _tail(output: str) -> str:
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip() and not _NOISE.match(ln)]
    return "\n".join(lines[-_FALLBACK_LINES:]) or "Dafny produced no output"