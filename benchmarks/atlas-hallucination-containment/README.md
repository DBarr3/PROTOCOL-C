# Atlas Hallucination-Containment Benchmark (Protocol-C attested)

A signed, tamper-evident record of an internal Aether Atlas experiment. The
numbers in [`manifest.json`](./manifest.json) were produced **on the Aether VPS5
(Oracle) node** and signed in-process with that node's Ed25519 Protocol-C key.
You can verify, without trusting us, that these exact numbers were attested by
the holder of that key and have not been edited since.

> **Honest scope.** This is **not** a public NLP hallucination benchmark
> (TruthfulQA, HaluEval, etc.). It measures one thing: how often the Atlas
> **surfacing gate** withholds a mislabelled / decayed ("hallucinated") cell
> before it can be served as a fact, on a controlled synthetic cell population.
> It is an engine-level containment measurement, not a model-level accuracy
> claim. We publish it because the *attestation* is the point: a number you can
> cryptographically tie to a run on our hardware.

## Result

| metric | value |
|---|---|
| containment mean (200 seeds) | **0.687** |
| sd | 0.066 |
| 5th-percentile floor (conservative) | **0.578** |
| median | 0.684 |
| range | 0.469 – 0.915 |
| Layer-1 admission reject-rate of hallucinated cells | **0.000** |

**Read it as:** the surfacing gate contains ~**69% ± 7%** of hallucinated cells;
quote the **p05 floor (≈58%)** if you want a single conservative number. The
admission gate (Layer 1) rejects *none* of them — containment is entirely a
**Layer-3 staleness / re-validation** effect, not an admission filter. We state
that explicitly rather than imply a multi-layer filter that isn't doing the work.

### Method (what each seed runs)

100 cells/seed, 50/50 correct vs. hallucinated, through the real pipeline:

```
admit  ->  surface  ->  append real outcome  ->  re-surface with contra_r
containment = 1 - surfaced_hallucinated / hallucinated
```

200 deterministic seeds (0–199). The single-seed baseline is locked at
`containment >= 0.50` in the engine's own test suite; this is the multi-seed band
around it. The Atlas engine that ran it is proprietary, so this is **reproducible
by attestation, not from scratch** — the signature is the guarantee, not a
re-run on your machine.

## Verify it yourself

```bash
pip install cryptography
python verify_manifest.py manifest.json
```

Three independent checks, all must pass:

1. `results_hash` — `sha256(canonical(results))` equals `results_sha256`
   (change one digit of any number → fails).
2. `attestation_bind` — the signed attestation commits to that same hash.
3. `ed25519_signature` — the signature verifies under the embedded
   `public_key_pem` (re-signing with a different key changes the fingerprint).

## Trust model

- **Signer:** VPS5 / Oracle node, Ed25519. The Oracle is the Atlas signing +
  audit authority, so a benchmark it signs carries the same provenance as an
  Atlas cell write.
- **Public-key fingerprint (anchor this):**
  `sha256(raw pubkey) = 920dd4c8559005db10e80cb127bce512e382ef7afc5e4a9f4189fd282fab79e7`
- **Engine identity:** `aether-atlas-deployed@vps5:d0de38aea90de664`
  (content hash of the deployed gate/core/store modules at run time).
- The private key never left the node; only the signature and public key are
  published here.

A valid signature proves the holder of the VPS5 Oracle key attested **these exact
numbers** at the recorded UTC. It does **not**, by itself, prove the key belongs
to Aether — anchor the fingerprint above against our published node key to close
that gap.

## What is deliberately NOT here

The Atlas LLM coding pool has a leakage-free SWE-bench *protocol*, but its current
input is a **synthetic** generator. We do **not** publish a SWE-bench
precision/F1 here, signed or otherwise, because a synthetic number is not a
benchmark result. That figure ships only after a real SWE-bench Verified run —
same attestation, real labels.
