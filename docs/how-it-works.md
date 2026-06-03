# How Protocol-C works

This is the long version of the README's "how it works" section. It walks the
full life of a commitment — from raw entropy to a verifiable on-disk receipt —
and explains *why* each step is shaped the way it is.

## The one-paragraph version

Protocol-C takes a dict, derives a fresh single-use signing key from CSPRNG
entropy, signs a canonical hash of the dict with secp256k1 ECDSA, immediately
zeroes the private key, and writes the result to an append-only log. To check a
record later you need only the public key embedded in the signature — no secret,
no server, no trust in the storage layer. Tampering is detected because any
change to the bytes breaks the signature; forgery is prevented because the key
that could sign a forgery no longer exists.

## The pipeline

```
get_seed()            commit(...)                         verify(...)
    │                     │                                   │
    ▼                     ▼                                   ▼
┌────────┐  seed  ┌───────────────┐  sig  ┌──────────────┐   ┌────────────┐
│ CSPRNG │ ─────▶ │ EphemeralKey  │ ────▶ │ commitment + │ ─▶│ ECDSA check│─▶ ✓ / ✗
│ 32 B   │        │ derive · sign │       │ signature    │   │ (pubkey)   │
└────────┘        │ · DESTROY     │       └──────┬───────┘   └────────────┘
                  └───────────────┘              │
                                                 ▼
                                          append-only JSONL
                                          + SQLite index
```

### 1. Entropy → seed

`get_seed()` calls `secrets.token_bytes(32)` — a cryptographically secure PRNG
seeded by the operating system. The result is 256 bits of unpredictable entropy.

Only the **hash** of the seed (`SHA-256`) is ever recorded, never the seed
itself. That hash is the `seed_commitment`: immutable proof that *a specific
measurement happened*, with nothing that could be used to reconstruct the key.

### 2. Seed → ephemeral key

The seed is turned into a secp256k1 private key by HMAC-SHA256 (domain-separated
with a fixed label), reduced modulo the curve order `N`. The matching public key
is the scalar multiplication `priv · G`.

This is the same curve Bitcoin uses, implemented from scratch in pure Python
(`ephemeral_signer.py`) so the entire signing path is auditable and carries no
third-party cryptography dependency.

The key is wrapped in a `QuantumEphemeralKey` that records a **temporal window**:
`created_at`, `expires_at` (default `created_at + 1 hour`), and
`shor_earliest_attack` (a conservative marker for the earliest plausible quantum
attack). The window is embedded in the signed structure so the safety argument
travels *with* the record.

### 3. Sign — once

The message dict is serialized to **canonical JSON** (`sort_keys=True`, compact
separators) and hashed with SHA-256. The signature is ECDSA over that hash, with
the nonce `k` chosen deterministically per **RFC 6979** and normalized to low-`s`
(BIP 62). Determinism matters twice over: it removes the catastrophic
nonce-reuse failure mode, and it makes signatures reproducible for audit.

The signature envelope carries everything a verifier needs:

```json
{
  "r": "<64 hex>",
  "s": "<64 hex>",
  "pubkey": "<33-byte compressed hex>",
  "algorithm": "ecdsa-secp256k1-sha256",
  "signed_at": "2026-06-03T00:00:00Z",
  "sign_count": 1
}
```

### 4. Destroy

The instant the signature is produced, the signer's `destroy()` runs: the private
key integer is set to `0` and the signer is marked destroyed. A second `sign()`
raises `KeyDestroyedError`. The public key is retained (it's not secret) so the
record stays verifiable forever.

This is the heart of the design. There is no long-lived private key anywhere in
the system — not on disk, not in a keyring, not in a process for longer than a
single signature. **The window in which the key exists is measured in
milliseconds.**

### 5. Record

If a `log_path` is given, the commitment is appended to a JSONL file — one
complete JSON object per line — and indexed in a companion SQLite database that
stores byte offsets for O(1) seeks and supports filtered queries by type,
timestamp, or method. The JSONL file is the source of truth; SQLite is a
rebuildable index. When the log passes a size threshold it is rotated with a
timestamp suffix.

### 6. Verify

`verify(commitment, signature)` rebuilds the public key from the envelope,
re-canonicalizes and re-hashes the commitment, and checks the ECDSA equation. It
needs **no private key and no original signer** — anyone holding the two JSON
objects can confirm the record. Change a single field of the commitment and the
recomputed hash won't match `r, s`, so verification returns `False`.

## Why this shape

| Decision | Reason |
|---|---|
| One key per commitment | Blast radius of any key compromise is exactly one record. |
| Destroy after one signature | No standing secret to steal; the quantum-safety argument reduces to "the key is gone." |
| RFC 6979 deterministic-k | Eliminates nonce-reuse key recovery; makes signatures reproducible for audit. |
| Canonical JSON + SHA-256 | Byte-stable verification across platforms and languages. |
| Append-only JSONL as truth | Storage you can put on write-once / object-lock media; SQLite stays a disposable index. |
| Pure-Python secp256k1 | Whole signing path is auditable; zero mandatory dependencies. |

## The three-phase chain

Decision → execution → settlement workflows get a commitment per phase, each with
its own independent seed and key:

| Phase | Class | Audit label |
|---|---|---|
| Commit the decision | `QuantumDecisionCommitment` | `DECISION_COMMITMENT` |
| Attest the execution | `QuantumExecutionAttestation` | `EXECUTION_ATTESTATION` |
| Record settlement | `QuantumSettlementRecord` | `SETTLEMENT_FINALITY` |

Because the phases are independently keyed, the chain is tamper-evident end to
end: you can prove what was decided, what was done, and how it settled — and that
none of the three was altered after the fact.

## What it is not

Protocol-C is a **commitment and audit** layer, not an encryption system and not
post-quantum cryptography. It does not hide the committed data (sign ≠ encrypt),
and its signature scheme is classical secp256k1. Its quantum-safety is the
temporal argument above, spelled out in full in [SECURITY.md](../SECURITY.md).
Read that before relying on the word "quantum-safe."

The quantum-hardware entropy variant is a separate, private project. This public
package is CSPRNG-only.
