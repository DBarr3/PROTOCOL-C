from aether_protocol_c.seed import QuantumSeedResult, generate_quantum_seed


def test_generate_returns_csprng_seed():
    r = generate_quantum_seed()
    assert isinstance(r, QuantumSeedResult)
    assert r.method == "CSPRNG"
    assert len(r.seed_hash) == 64
    assert isinstance(r.seed_int, int)


def test_seeds_are_independent():
    seeds = [generate_quantum_seed() for _ in range(5)]
    assert len({s.seed_hash for s in seeds}) == 5


def test_no_ibm_or_qiskit_symbols():
    import aether_protocol_c.seed as s
    src = open(s.__file__, encoding="utf-8").read().lower()
    for bad in ("qiskit", "ibm", "aer_simulator", "credential"):
        assert bad not in src, f"residual '{bad}' in seed.py"
