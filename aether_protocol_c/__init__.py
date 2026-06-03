"""
aether-protocol-c  --  CSPRNG Quantum-Safe Commitment Protocol
================================================================

A standalone, pip-installable library for creating cryptographically
signed, quantum-safe data commitments with full audit trails.

Quick start::

    from aether_protocol_c import commit, verify, get_seed

    seed  = get_seed()
    rec   = commit(seed, order_id="order_001",
                   trade_details={"symbol": "BTC", "qty": 1, "side": "long", "price": 50000},
                   account_state={"capital": 100000, "equity": 100000,
                                  "open_positions": [], "risk_used": 0.0,
                                  "risk_limit": 1.0, "nonce": 1,
                                  "timestamp": 0})
    assert rec["verified"]

Protocol-C uses CSPRNG (secrets.token_bytes) for all entropy.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    # ── High-level API ──────────────────────────────────────────
    "commit",
    "verify",
    "batch_commit",
    "get_seed",
    # ── Core classes ────────────────────────────────────────────
    "QuantumEphemeralKey",
    "QuantumSeedCommitment",
    "QuantumDecisionCommitment",
    "ReasoningCapture",
    "AccountSnapshot",
    "AuditLog",
    "EphemeralSigner",
    # ── Backend ─────────────────────────────────────────────────
    "QuantumSeedResult",
    "generate_quantum_seed",
    # ── Verification ────────────────────────────────────────────
    "verify_signature",
    "AuditVerifier",
    # ── Timestamp ───────────────────────────────────────────────
    "RFC3161TimestampAuthority",
]

# ── Re-exports ───────────────────────────────────────────────────────
from .crypto import (
    QuantumEphemeralKey,
    QuantumSeedCommitment,
    verify_signature,
    get_quantum_seed,
    make_temporal_window,
)
from .ephemeral_signer import EphemeralSigner
from .commitment import QuantumDecisionCommitment, ReasoningCapture
from .state import AccountSnapshot
from .audit import AuditLog
from .seed import QuantumSeedResult, generate_quantum_seed
from .verify import AuditVerifier
from .timestamp_authority import RFC3161TimestampAuthority


# ── Convenience functions ────────────────────────────────────────────

def get_seed(method: str = "CSPRNG", **kwargs) -> QuantumSeedResult:
    """
    Generate a cryptographic seed.

    Args:
        method: Entropy source (default "CSPRNG").

    Returns:
        QuantumSeedResult with full provenance metadata.
    """
    return generate_quantum_seed(method=method, **kwargs)


def commit(
    seed: QuantumSeedResult,
    *,
    order_id: str,
    trade_details: dict,
    account_state: dict,
    reasoning_text: str | None = None,
    reasoning_model: str = "human",
    log_path: str | None = None,
) -> dict:
    """
    Create a signed commitment and optionally append to an audit log.

    Args:
        seed: Seed from get_seed().
        order_id: Unique identifier for the commitment.
        trade_details: Dict describing what is being committed.
        account_state: Dict with capital, equity, open_positions,
            risk_used, risk_limit, nonce, timestamp.
        reasoning_text: Optional reasoning to bind cryptographically.
        reasoning_model: Source of the reasoning (default "human").
        log_path: Optional path to audit log JSONL file.

    Returns:
        Dict with commitment, signature, seed_info, and verified flag.
    """
    snap = AccountSnapshot.from_dict(account_state)

    reasoning = None
    if reasoning_text:
        reasoning = ReasoningCapture.from_text(
            reasoning_text, model=reasoning_model
        )

    c_dict, c_sig, _ = QuantumDecisionCommitment.create_and_sign(
        order_id=order_id,
        trade_details=trade_details,
        account_state=snap,
        quantum_seed=seed.seed_int,
        measurement_method=seed.method,
        reasoning=reasoning,
    )

    # Optionally log
    if log_path:
        audit = AuditLog(log_path)
        audit.append_commitment(c_dict, c_sig)

    # Verify
    verified = verify_signature(c_dict, c_sig)

    return {
        "commitment": c_dict,
        "signature": c_sig,
        "seed_info": seed.to_dict(),
        "verified": verified,
    }


def verify(commitment: dict, signature: dict) -> bool:
    """
    Verify a commitment signature.

    Args:
        commitment: The commitment dict.
        signature: The signature envelope.

    Returns:
        True if signature is valid.
    """
    return verify_signature(commitment, signature)


def batch_commit(
    items: list[dict],
    *,
    log_path: str | None = None,
) -> list[dict]:
    """
    Commit multiple items, each with its own independent seed.

    Args:
        items: List of dicts, each with keys: order_id, trade_details,
            account_state. Optional: reasoning_text, reasoning_model.
        log_path: Optional audit log path.

    Returns:
        List of commitment result dicts.
    """
    results = []
    for item in items:
        seed = get_seed()
        result = commit(
            seed,
            order_id=item["order_id"],
            trade_details=item["trade_details"],
            account_state=item["account_state"],
            reasoning_text=item.get("reasoning_text"),
            reasoning_model=item.get("reasoning_model", "human"),
            log_path=log_path,
        )
        results.append(result)
    return results
