import io, json, sys
from aether_protocol_c.cli import main


def _run(argv, out=None):
    out = out or io.StringIO()
    return main(argv, out=out), out.getvalue()


def _seed_log(tmp_path):
    log = tmp_path / "audit.jsonl"
    payload = {"order_id": "log_1",
               "trade_details": {"symbol": "BTC", "qty": 1, "side": "long", "price": 50000},
               "account_state": {"capital": 100000, "equity": 100000, "open_positions": [],
                                 "risk_used": 0.0, "risk_limit": 1.0, "nonce": 1, "timestamp": 0}}
    old = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        main(["commit", "--log", str(log)], out=io.StringIO())
    finally:
        sys.stdin = old
    return log


def test_logs_lists_entries(tmp_path):
    log = _seed_log(tmp_path)
    code, out = _run(["logs", "--log", str(log)])
    assert code == 0
    data = json.loads(out)
    assert data["count"] >= 1
    assert data["entries"][0]["order_id"] == "log_1"


def test_logs_verify_passes_for_genuine_entry(tmp_path):
    log = _seed_log(tmp_path)
    code, out = _run(["logs", "--log", str(log), "--verify"])
    data = json.loads(out)
    assert data["invalid"] == 0   # a real committed entry must verify VALID
    assert code == 0


def test_logs_verify_flags_tamper(tmp_path):
    log = _seed_log(tmp_path)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"order_id": "evil", "data": {"x": 1},
                             "signature": {"r": "0"*64, "s": "0"*64,
                                           "pubkey": "02"+"0"*64,
                                           "algorithm": "ecdsa-secp256k1-sha256"}}) + "\n")
    code, out = _run(["logs", "--log", str(log), "--verify"])
    data = json.loads(out)
    assert data["invalid"] >= 1
    assert code == 1  # tamper detected -> nonzero exit


def test_logs_verify_skips_system_rotation_entry(tmp_path):
    log = _seed_log(tmp_path)
    # A LOG_ROTATION marker legitimately carries no signature; it must NOT be
    # counted as tampering by --verify.
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"phase": "LOG_ROTATION", "order_id": None,
                             "data": {"reason": "size"}, "signature": {}}) + "\n")
    code, out = _run(["logs", "--log", str(log), "--verify"])
    data = json.loads(out)
    assert data["invalid"] == 0   # rotation marker skipped, not flagged
    assert code == 0
