import io, json
from aether_protocol_c.cli import main


def test_info_reports_csprng_and_version():
    out = io.StringIO()
    code = main(["info"], out=out)
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["entropy_source"] == "CSPRNG"
    assert "version" in data
    assert data["key_lifetime_seconds"] == 3600
    assert "python" in data
