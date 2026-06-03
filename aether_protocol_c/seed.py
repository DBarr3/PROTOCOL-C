"""
aether_protocol_c/seed.py

CSPRNG seed generation for Protocol-C.

Protocol-C derives every ephemeral signing key from a fresh, cryptographically
secure random seed produced by the operating system via :mod:`secrets`. There
is no external entropy source and no third-party dependency. Hardware
entropy sources are outside the scope of this library.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class QuantumSeedResult:
    """
    Immutable result of a seed generation.

    Fields:
        seed_int: The seed as an integer (consumed by the ephemeral signer).
        seed_hash: SHA-256 hex digest of the 32-byte seed (the public commitment
            to the seed; the raw seed is never stored or transmitted).
        method: Entropy source label. Always ``"CSPRNG"`` in Protocol-C.
    """

    seed_int: int
    seed_hash: str
    method: str = "CSPRNG"

    def to_dict(self) -> dict:
        """Serialise the provenance metadata (never includes the raw seed)."""
        return {"seed_hash": self.seed_hash, "method": self.method}


def generate_quantum_seed(method: str = "CSPRNG", **_ignored) -> QuantumSeedResult:
    """
    Generate a 256-bit CSPRNG seed.

    The ``method`` argument is accepted for API compatibility but Protocol-C
    always uses ``secrets.token_bytes`` (CSPRNG); any other value is ignored.

    Returns:
        A :class:`QuantumSeedResult` with the seed int, its SHA-256 hash, and
        the method label ``"CSPRNG"``.
    """
    seed_bytes = secrets.token_bytes(32)
    seed_int = int.from_bytes(seed_bytes, "big")
    seed_hash = hashlib.sha256(seed_bytes).hexdigest()
    return QuantumSeedResult(seed_int=seed_int, seed_hash=seed_hash, method="CSPRNG")
