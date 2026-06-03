from pathlib import Path

from ai_economics_cockpit.cli import cmd_all


def snapshot(path: Path):
    if not path.exists():
        return None
    return (path.stat().st_mtime_ns, path.stat().st_size)


def test_no_cross_repo_mutation():
    paths = [
        Path("/Users/liberel/code/macro-dataops/README.md"),
        Path("/Users/liberel/code/uk-inflation-cockpit/README.md"),
    ]
    before = [snapshot(p) for p in paths]
    cmd_all()
    after = [snapshot(p) for p in paths]
    assert before == after

