import pathlib
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_pyproject_clean():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    proj = data["project"]
    assert proj["name"] == "aether-protocol-c"
    assert proj["dependencies"] == []
    extras = proj.get("optional-dependencies", {})
    assert set(extras) <= {"timestamp", "dev"}, f"unexpected extras: {set(extras)}"
    assert "quantum" not in extras and "server" not in extras
    assert proj["scripts"]["aether-protocol-c"] == "aether_protocol_c.cli:main"
    urls = " ".join(proj["urls"].values()).lower()
    assert "aether-technologies" not in urls
