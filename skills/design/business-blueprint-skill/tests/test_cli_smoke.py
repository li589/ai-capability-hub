import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "business_blueprint.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_help_lists_supported_commands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "--plan" in result.stdout
    assert "--generate" in result.stdout
    assert "--validate" in result.stdout
