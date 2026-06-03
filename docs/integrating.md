# Integrating Protocol-C into your app

Add signed, tamper-evident audit logging to any Python app in ~5 lines.

## The 5-line drop-in

```python
from aether_protocol_c import commit, get_seed

def record_decision(order_id, details, account_state):
    return commit(get_seed(), order_id=order_id,
                  trade_details=details, account_state=account_state,
                  log_path="audit/audit.jsonl")
```

Every call appends a signed record to `audit/audit.jsonl`. Audit it anytime:

```bash
aether-protocol-c logs --log audit/audit.jsonl --verify
```

## Loggable event types

| Event type | When to record it |
|---|---|
| `DECISION_COMMITMENT` | Before an action — what was decided and why. |
| `EXECUTION_ATTESTATION` | After acting — what actually happened. |
| `SETTLEMENT_FINALITY` | On finalize — the sealed outcome. |
| `commit` (generic) | Any single-shot decision receipt. |
| custom `record_type` | App-defined events through the same signed audit API. |

For decision -> execution -> settlement workflows, use the three-phase API
(`QuantumDecisionCommitment`, `QuantumExecutionAttestation`,
`QuantumSettlementRecord`) so each phase is independently keyed and the whole
chain is tamper-evident. See [how-it-works.md](how-it-works.md).
