import io, json
from aether_protocol_c.cli import main


def test_demo_runs_commit_verify_end_to_end():
    out = io.StringIO()
    code = main(["demo"], out=out)
    assert code == 0
    data = json.loads(out.getvalue())
    assert data["verified"] is True
    assert data["commitment"]["order_id"].startswith("demo")
