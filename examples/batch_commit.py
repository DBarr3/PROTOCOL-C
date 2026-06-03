#!/usr/bin/env python3
"""
batch_commit.py -- Batch commitment with audit logging.

Creates multiple commitments with independent seeds, logs them to
an audit file, and verifies each one.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aether_protocol_c import batch_commit, AuditLog


def main():
    # Use a temp file for the audit log
    log_path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")

    items = [
        {
            "order_id": f"batch_{i:03d}",
            "trade_details": {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "price": price,
            },
            "account_state": {
                "capital": 100_000,
                "equity": 100_000,
                "open_positions": [],
                "risk_used": 0.0,
                "risk_limit": 1.0,
                "nonce": i + 1,
                "timestamp": 0,
            },
        }
        for i, (symbol, qty, side, price) in enumerate([
            ("BTC", 1, "long", 50_000),
            ("ETH", 10, "short", 3_200),
            ("SOL", 100, "long", 145),
            ("AAPL", 50, "long", 185),
            ("YM", 5, "short", 39_000),
        ])
    ]

    print(f"Committing {len(items)} items with independent seeds...\n")

    results = batch_commit(items, log_path=log_path)

    for r in results:
        oid = r["commitment"]["order_id"]
        sym = r["commitment"]["trade_details"]["symbol"]
        ok = r["verified"]
        seed_hash = r["seed_info"]["seed_hash"][:12]
        print(f"  {oid}: {sym:5s} | verified={ok} | seed={seed_hash}...")

    # Verify all seeds are independent (different hashes)
    seed_hashes = {r["seed_info"]["seed_hash"] for r in results}
    assert len(seed_hashes) == len(results), "Seed reuse detected!"
    print(f"\nAll {len(results)} seeds are independent (unique hashes).")

    # Verify audit log
    audit = AuditLog(log_path)
    entries = audit.read_all()
    print(f"Audit log: {len(entries)} entries written to {log_path}")

    print("\nAll batch checks passed.")


if __name__ == "__main__":
    main()
