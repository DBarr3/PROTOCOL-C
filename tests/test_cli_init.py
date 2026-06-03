import io, json
from aether_protocol_c.cli import main


def _run(argv):
    out = io.StringIO()
    code = main(argv, out=out)
    return code, out.getvalue()


def test_init_scaffolds_config_and_audit_dir(tmp_path):
    code, out = _run(["init", "--dir", str(tmp_path)])
    assert code == 0
    cfg = tmp_path / "aether.config.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["entropy"] == "CSPRNG"
    assert (tmp_path / "audit").is_dir()


def test_init_refuses_clobber_without_force(tmp_path):
    _run(["init", "--dir", str(tmp_path)])
    code, _ = _run(["init", "--dir", str(tmp_path)])
    assert code == 2  # refuse overwrite


def test_init_force_overwrites(tmp_path):
    _run(["init", "--dir", str(tmp_path)])
    code, _ = _run(["init", "--dir", str(tmp_path), "--force"])
    assert code == 0
