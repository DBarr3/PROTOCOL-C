import pathlib

PKG = pathlib.Path(__file__).resolve().parent.parent / "aether_protocol_c"
BANNED = ("qiskit", "ibm_quantum", "ibm quantum", "aer_simulator",
          "protocol-l", "protocol_l", "aether-protocol-l", "predator",
          "aether-cloud", "tailscale", "wireguard")


def test_package_has_no_protocol_l_residue():
    offenders = []
    for py in PKG.glob("*.py"):
        text = py.read_text(encoding="utf-8").lower()
        for bad in BANNED:
            if bad in text:
                offenders.append(f"{py.name}: {bad}")
    assert not offenders, "Protocol-L residue:\n" + "\n".join(offenders)
