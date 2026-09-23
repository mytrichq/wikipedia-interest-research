import subprocess
from pathlib import Path

from wir import __version__
from wir.cli import main

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_help_exits_cleanly(capsys):
    assert main([]) == 0
    assert "Wikipedia Interest Research" in capsys.readouterr().out


def test_wrapper_script_runs_from_any_cwd(tmp_path):
    result = subprocess.run(
        [str(SKILL_DIR / "scripts" / "wir"), "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == f"wir {__version__}"
