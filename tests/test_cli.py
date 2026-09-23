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


def test_packaged_skill_runs_without_dev_files(tmp_path):
    """The skill as installed (shipped files only) must work on its own."""
    import sys

    sys.path.insert(0, str(SKILL_DIR / "evals"))
    from claude_code import SKILL_NAME, package_skill

    packaged = tmp_path / SKILL_NAME
    package_skill(packaged)
    result = subprocess.run(
        [str(packaged / "scripts" / "wir"), "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"wir {__version__}"
