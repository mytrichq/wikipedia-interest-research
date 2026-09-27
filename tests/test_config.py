from wir import config


def test_studies_go_to_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WIR_STUDIES", raising=False)
    assert config.studies_root() == tmp_path.resolve() / "wiki-studies"


def test_agent_that_cds_into_an_installed_skill_still_saves_in_the_project(tmp_path, monkeypatch):
    skill = tmp_path / "project" / ".claude" / "skills" / "wikipedia-interest-research"
    skill.mkdir(parents=True)
    monkeypatch.chdir(skill)
    monkeypatch.setenv("PWD", str(skill))
    monkeypatch.delenv("WIR_STUDIES", raising=False)
    assert config.studies_root() == (tmp_path / "project").resolve() / "wiki-studies"


def test_running_from_the_skill_source_uses_the_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PWD", str(tmp_path))
    monkeypatch.delenv("WIR_STUDIES", raising=False)
    assert config.studies_root() == tmp_path.resolve() / "wiki-studies"


def test_explicit_location_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("WIR_STUDIES", str(tmp_path / "mine"))
    assert config.studies_root() == tmp_path / "mine"
