#!/usr/bin/env python3
"""
basic_commit.py -- Minimal usage of aether-protocol-c.

Creates a single commitment, verifies the signature, and prints the result.
"""

import json
import sys
import os

# Allow running from repo root without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aether_protocol_c import commit, verify, get_seed


def main():
    # 1. Generate a CSPRNG seed
    seed = get_seed()
    print(f"[1] Seed generated: method={seed.method}, hash={seed.seed_hash[:16]}...")

    # 2. Create a signed commitment
    result = commit(
        seed,
        order_id="order_001",
        trade_details={
            "symbol": "BTC",
            "qty": 1,
            "side": "long",
            "price": 50_000,
        },
        account_state={
            "capital": 100_000,
            "equity": 100_000,
            "open_positions": [],
            "risk_used": 0.0,
            "risk_limit": 1.0,
            "nonce": 1,
            "timestamp": 0,
        },
    )

    print(f"[2] Commitment created for order: {result['commitment']['order_id']}")
    print(f"    Signature algorithm: {result['signature']['algorithm']}")
    print(f"    Public key: {result['signature']['pubkey'][:24]}...")
    print(f"    Seed method: {result['seed_info']['method']}")
    print(f"    Verified: {result['verified']}")

    # 3. Independent verification
    ok = verify(result["commitment"], result["signature"])
    print(f"[3] Independent verify: {ok}")

    # 4. Show quantum safety window
    window = result["commitment"]["key_temporal_window"]
    lifetime_hours = (window["expires_at"] - window["created_at"]) / 3600
    safety_days = (window["shor_earliest_attack"] - window["expires_at"]) / 86400
    print(f"[4] Key lifetime: {lifetime_hours:.1f} hours")
    print(f"    Safety margin before Shor's: {safety_days:.1f} days")

    assert result["verified"], "Commitment verification failed!"
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
