# Security Policy

Protocol-C is a cryptographic commitment library. This document states what it
does and does not protect against, and how to report a vulnerability.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, use GitHub's private vulnerability reporting:
**Security → Report a vulnerability** on the
[repository](https://github.com/DBarr3/protocol-c/security/advisories/new),
or email the maintainer at the address listed on
[aethersystems.net](https://aethersystems.net).

Please include a description, reproduction steps, and impact. We aim to
acknowledge reports within a few days and to coordinate a fix and disclosure
timeline with you.

## Supported versions

Protocol-C is pre-1.0. Security fixes target the latest released version and
`main`. Pin a version in production and watch releases.

## Threat model

**What Protocol-C protects:**

- **Integrity / tamper-evidence.** Any modification to committed data
  invalidates its signature. A stored commitment cannot be silently altered.
- **Non-repudiation.** A valid signature proves the committed bytes existed and
  were signed by the holder of the ephemeral key at signing time.
- **Forward secrecy.** Each commitment uses an independent CSPRNG seed and a
  single-use key whose private half is zeroed immediately after signing.
  Compromise of one commitment's key reveals nothing about others.

**What Protocol-C does NOT provide:**

- **Post-quantum cryptography.** secp256k1 ECDSA is not quantum-resistant. See
  "On 'quantum-safe'" below. If you need standardized PQC signatures
  (ML-DSA / SLH-DSA), this is not a drop-in.
- **Confidentiality.** Commitments are signed, not encrypted. Do not put secrets
  in the committed payload; the data is recoverable from the audit log.
- **Trusted timestamping by default.** The temporal window uses local system
  time. For third-party-verifiable time, use the optional `[timestamp]` extra
  (RFC 3161) or an external timestamp authority.
- **Key custody for long-lived identities.** There is intentionally no long-lived
  private key to manage — that's the design. If you need a stable signing
  identity, layer it above Protocol-C.

## On "quantum-safe"

The "quantum-safe" claim is a **temporal-safety** argument, not a claim of
post-quantum security:

- The signature scheme (secp256k1 ECDSA) is classical and would be breakable by a
  sufficiently large fault-tolerant quantum computer running Shor's algorithm.
  No such machine exists today; breaking secp256k1 is estimated to require on the
  order of thousands of logical qubits.
- Protocol-C's mitigation is that the **private key is destroyed within ~1 hour
  (default, configurable) of creation** — far inside any plausible attack window.
  Shor's algorithm needs the key to exist to be useful; a zeroed key cannot be
  recovered. The defense is the key's *absence*, not the algorithm's strength.

Treat Protocol-C as a **forward-secret, tamper-evident commitment layer** with a
documented temporal margin — not as post-quantum cryptography.

This public package is **CSPRNG-only**: all entropy comes from
`secrets.token_bytes`. The quantum-hardware entropy variant is a separate,
private project and ships no code here.

## Cryptographic implementation notes

- **Signer:** original pure-Python secp256k1 ECDSA in `ephemeral_signer.py`,
  using RFC 6979 deterministic-k (eliminates nonce-reuse) and BIP 62 low-s
  normalization. No third-party crypto library is used in the core path.
- **Key derivation:** the private key is derived from seed entropy via
  HMAC-SHA256, reduced mod the curve order `N`.
- **Canonicalization:** messages are signed over canonical JSON
  (`sort_keys=True`, compact separators) hashed with SHA-256, so verification is
  byte-stable across platforms.
- **Audit log:** append-only JSONL is the source of truth; the SQLite companion
  is an index only. Treat the JSONL file as immutable in storage (write-once
  media or object-lock buckets recommended for high-assurance use).

If you find a flaw in any of the above, please report it privately as described
at the top of this document.
