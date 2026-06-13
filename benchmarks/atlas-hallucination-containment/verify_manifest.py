"""bench/verify_manifest.py
===========================
Standalone verifier for a Protocol-C benchmark manifest. PUBLIC — ships with the
published benchmark so anyone can check the result was signed by the node key and
not edited after the fact.

Three independent checks:
  1. results hash      — sha256(canonical(manifest.results)) == manifest.results_sha256
  2. attestation bind  — manifest.attestation.results_sha256 == that same hash
  3. signature         — Ed25519 verify(signature, canonical(attestation)) under public_key_pem

Pass all three and the numbers in `results` are exactly what the holder of
`public_key_pem` signed. Change a single digit and check 1 fails; re-sign with a
different key and the published public-key fingerprint no longer matches the one
anchored in the node's infra.

    python verify_manifest.py manifest.json

Only dependency outside the stdlib is `cryptography` (pip install cryptography).
"""
from __future__ import annotations

import hashlib
import json
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify(manifest: dict) -> list:
    """Return a list of (check_name, ok, detail)."""
    checks = []

    results_hash = hashlib.sha256(_canonical(manifest["results"])).hexdigest()
    checks.append((
        "results_hash",
        results_hash == manifest["results_sha256"],
        f"{results_hash} vs {manifest['results_sha256']}",
    ))

    att = manifest["attestation"]
    checks.append((
        "attestation_bind",
        att.get("results_sha256") == manifest["results_sha256"],
        f"attestation binds {att.get('results_sha256')}",
    ))

    ok_sig = False
    detail = ""
    try:
        pub = serialization.load_pem_public_key(manifest["public_key_pem"].encode("ascii"))
        if not isinstance(pub, Ed25519PublicKey):
            detail = f"not an Ed25519 public key ({type(pub).__name__})"
        else:
            pub.verify(bytes.fromhex(manifest["signature_ed25519"]), _canonical(att))
            ok_sig = True
            detail = f"signed by pubkey_sha256={manifest.get('public_key_sha256', '?')}"
    except InvalidSignature:
        detail = "INVALID signature for this public key"
    except Exception as e:  # noqa: BLE001
        detail = f"error: {e}"
    checks.append(("ed25519_signature", ok_sig, detail))

    return checks


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python verify_manifest.py manifest.json", file=sys.stderr)
        return 2
    with open(argv[0], "rb") as fh:
        manifest = json.loads(fh.read())

    checks = verify(manifest)
    print(f"benchmark: {manifest.get('benchmark')}")
    print(f"node:      {manifest.get('attestation', {}).get('node')}  "
          f"utc: {manifest.get('attestation', {}).get('utc')}")
    print(f"engine:    {manifest.get('attestation', {}).get('engine')}")
    print("-" * 56)
    all_ok = True
    for name, ok, detail in checks:
        all_ok = all_ok and ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print("-" * 56)
    print("VERDICT:", "VERIFIED -- signed, unmodified." if all_ok else "FAILED -- do not trust.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
