"""
tests/test_cli.py -- Tests for the aether-protocol-c command-line interface.

Covers the seed/commit/verify subcommands, stdin and file input, exit codes,
and error handling. The CLI is a thin wrapper over the library, so these
tests focus on argument wiring, IO, and exit-code contracts.
"""

import io
import json

import pytest

from aether_protocol_c.cli import build_parser, main


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def order_payload():
    """A minimal valid commit payload."""
    return {
        "order_id": "cli_test_001",
        "trade_details": {"symbol": "BTC", "qty": 1, "side": "long", "price": 50000},
        "account_state": {
            "capital": 100000, "equity": 100000, "open_positions": [],
            "risk_used": 0.0, "risk_limit": 1.0, "nonce": 1, "timestamp": 0,
        },
    }


def _run(argv, stdin_text=None, monkeypatch=None):
    """Run the CLI, optionally feeding stdin, and capture stdout JSON + exit code."""
    if stdin_text is not None and monkeypatch is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    out = io.StringIO()
    code = main(argv, out=out)
    return code, out.getvalue()


# ── seed ──────────────────────────────────────────────────────────────────────

def test_seed_emits_provenance_json():
    # Arrange / Act
    code, output = _run(["seed"])

    # Assert
    assert code == 0
    data = json.loads(output)
    assert data["method"] == "CSPRNG"
    assert len(data["seed_hash"]) == 64


# ── commit ────────────────────────────────────────────────────────────────────

def test_commit_from_stdin_verifies(order_payload, monkeypatch):
    # Arrange / Act
    code, output = _run(
        ["commit"], stdin_text=json.dumps(order_payload), monkeypatch=monkeypatch
    )

    # Assert
    assert code == 0
    result = json.loads(output)
    assert result["verified"] is True
    assert result["commitment"]["order_id"] == "cli_test_001"


def test_commit_from_file_verifies(order_payload, tmp_path):
    # Arrange
    payload_file = tmp_path / "order.json"
    payload_file.write_text(json.dumps(order_payload), encoding="utf-8")

    # Act
    code, output = _run(["commit", "--file", str(payload_file)])

    # Assert
    assert code == 0
    assert json.loads(output)["verified"] is True


def test_commit_writes_audit_log(order_payload, tmp_path, monkeypatch):
    # Arrange
    log_path = tmp_path / "audit.jsonl"

    # Act
    code, _ = _run(
        ["commit", "--log", str(log_path)],
        stdin_text=json.dumps(order_payload),
        monkeypatch=monkeypatch,
    )

    # Assert
    assert code == 0
    assert log_path.exists()
    first_line = log_path.read_text(encoding="utf-8").splitlines()[0]
    assert json.loads(first_line)["order_id"] == "cli_test_001"


def test_commit_missing_key_errors(monkeypatch):
    # Arrange: payload missing account_state
    bad = {"order_id": "x", "trade_details": {}}

    # Act
    code, _ = _run(
        ["commit"], stdin_text=json.dumps(bad), monkeypatch=monkeypatch
    )

    # Assert
    assert code == 2


# ── verify ────────────────────────────────────────────────────────────────────

def test_verify_roundtrip_through_cli(order_payload, monkeypatch):
    # Arrange: produce a real commitment via the commit command
    _, commit_out = _run(
        ["commit"], stdin_text=json.dumps(order_payload), monkeypatch=monkeypatch
    )
    result = json.loads(commit_out)
    envelope = {
        "commitment": result["commitment"],
        "signature": result["signature"],
    }

    # Act
    code, verify_out = _run(
        ["verify"], stdin_text=json.dumps(envelope), monkeypatch=monkeypatch
    )

    # Assert
    assert code == 0
    assert json.loads(verify_out)["verified"] is True


def test_verify_detects_tampering(order_payload, monkeypatch):
    # Arrange: tamper with the committed payload
    _, commit_out = _run(
        ["commit"], stdin_text=json.dumps(order_payload), monkeypatch=monkeypatch
    )
    result = json.loads(commit_out)
    tampered = dict(result["commitment"])
    tampered["order_id"] = "tampered_999"
    envelope = {"commitment": tampered, "signature": result["signature"]}

    # Act
    code, verify_out = _run(
        ["verify"], stdin_text=json.dumps(envelope), monkeypatch=monkeypatch
    )

    # Assert
    assert code == 1
    assert json.loads(verify_out)["verified"] is False


# ── parser / surface ──────────────────────────────────────────────────────────

def test_no_command_returns_usage_exit_code():
    # Act
    code = main([])

    # Assert
    assert code == 2


def test_parser_exposes_all_subcommands():
    # Act
    parser = build_parser()
    subactions = [
        a for a in parser._actions if hasattr(a, "choices") and a.choices
    ]

    # Assert
    choices = set()
    for action in subactions:
        choices.update(action.choices.keys())
    assert {"seed", "commit", "verify"} <= choices
