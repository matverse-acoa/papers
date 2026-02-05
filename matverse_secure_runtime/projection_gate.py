from typing import Mapping, Any


def projection_gate(state: Mapping[str, Any], psi_min: float = 0.85, cvar_max: float = 0.05) -> None:
    psi = state.get("psi")
    cvar = state.get("cvar")

    if psi is None or psi < psi_min:
        raise SystemExit(f"FAIL-CLOSED: constitutional violation Ψ={psi} < {psi_min}")

    if cvar is None or cvar > cvar_max:
        raise SystemExit(f"FAIL-CLOSED: constitutional violation CVaR={cvar} > {cvar_max}")
