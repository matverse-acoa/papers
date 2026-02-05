def projection_gate(state: dict):
    """
    HARD FAIL constitutional gate.
    Nenhum estado inválido entra no ledger.
    """
    psi = state.get("psi")
    cvar = state.get("cvar")

    if psi is None or psi < 0.85:
        raise RuntimeError("CONSTITUTIONAL VIOLATION: Ψ < 0.85")

    if cvar is None or cvar > 0.05:
        raise RuntimeError("CONSTITUTIONAL VIOLATION: CVaR > 0.05")

    return True
