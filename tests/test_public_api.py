import importlib.util
import aether_protocol_c as ap


def test_high_level_api_present():
    for name in ("commit", "verify", "batch_commit", "get_seed",
                 "QuantumDecisionCommitment", "AccountSnapshot", "AuditLog",
                 "EphemeralSigner", "QuantumSeedResult", "verify_signature"):
        assert hasattr(ap, name), f"missing public symbol: {name}"


def test_private_modules_not_imported():
    for gone in ("async_protocol", "session", "server", "backend"):
        assert importlib.util.find_spec(f"aether_protocol_c.{gone}") is None, \
            f"{gone} should not exist in the public package"


def test_get_seed_roundtrip():
    s = ap.get_seed()
    assert s.method == "CSPRNG"
