# Changelog

## [0.1.0] - 2026-06-03

### Added
- Initial public release of Protocol-C: CSPRNG, forward-secret, tamper-evident
  data commitments.
- High-level API: `get_seed`, `commit`, `verify`, `batch_commit`.
- Pure-Python secp256k1 ECDSA signer (RFC 6979) with one-shot ephemeral keys
  destroyed immediately after signing.
- Three-phase chain: decision commitment, execution attestation, settlement.
- Append-only JSONL audit log with SQLite indexing.
- CLI: `seed`, `commit`, `verify`, `init`, `info`, `demo`, `logs`.
- Optional `[timestamp]` extra (RFC 3161).
