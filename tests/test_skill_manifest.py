import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter() -> dict[str, str]:
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must start with a YAML frontmatter block"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def test_name_follows_spec_and_matches_directory():
    name = frontmatter()["name"]
    assert 1 <= len(name) <= 64
    assert NAME_RE.match(name), "lowercase letters, digits and single hyphens only"
    assert name == SKILL_DIR.name, "name must match the skill directory name"


def test_description_within_limits():
    description = frontmatter()["description"]
    assert 1 <= len(description) <= 1024
    assert "<" not in description and ">" not in description, "no XML tags"


def test_compatibility_within_limits():
    assert len(frontmatter().get("compatibility", "")) <= 500


def test_skill_md_stays_small():
    assert len(SKILL_MD.read_text(encoding="utf-8").splitlines()) < 500
