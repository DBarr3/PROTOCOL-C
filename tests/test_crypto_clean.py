import aether_protocol_c.crypto as c


def test_get_quantum_seed_is_csprng_only():
    seed_int, method = c.get_quantum_seed()
    assert method == "CSPRNG"
    assert isinstance(seed_int, int)


def test_crypto_has_no_ibm_paths():
    src = open(c.__file__, encoding="utf-8").read().lower()
    for bad in ("qiskit", "ibm_quantum", "aer_simulator", "_seed_pool", "protocol-l", "protocol_l"):
        assert bad not in src, f"residual '{bad}' in crypto.py"
