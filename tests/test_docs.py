"""The docs point at things that exist: README links, and each script's usage lines."""

import re

import pytest

from conftest import ROOT

SCRIPTS = sorted(p for d in ("python", "langchain") for p in (ROOT / d).glob("*/*.py"))
READMES = sorted(p for p in ROOT.glob("**/README.md")
                 if not any(part.startswith(".") for part in p.relative_to(ROOT).parts))


@pytest.mark.parametrize("readme", READMES, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(readme):
    text = readme.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#]+)\)", text):
        if "://" in target or target.startswith("mailto:"):
            continue
        assert (readme.parent / target).exists(), f"{readme.name} links to missing {target}"


def test_every_example_is_in_the_readme_table():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    folders = {p.parent.relative_to(ROOT).as_posix() for p in SCRIPTS}
    folders |= {p.relative_to(ROOT).as_posix() for p in (ROOT / "mcp").iterdir() if p.is_dir()}
    for folder in folders:
        assert f"]({folder}/)" in text, f"README.md does not list {folder}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_usage_lines_name_the_script_itself(script):
    usage = re.findall(r"python (\S+\.py)", script.read_text(encoding="utf-8"))
    assert usage, f"{script.name} has no usage line"
    assert set(usage) == {script.name}


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_every_script_has_a_dry_run(script):
    assert '"--dry-run"' in script.read_text(encoding="utf-8")
