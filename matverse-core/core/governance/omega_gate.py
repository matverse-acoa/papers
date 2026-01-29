"""
Ω-GATE - Mathematical Governance Gate
Implementation of invariant-based decision system
"""

import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


@dataclass
class GovernanceMetrics:
    """Metrics for Ω-GATE decision making"""
    psi: float  # Coherence index [0, 1]
    theta: float  # Performance score [0, 1]
    cvar: float  # Conditional Value at Risk [0, 1]
    alpha: float  # Antifragility index [0, ∞]
    completeness: float  # Completeness [0, 1]
    consistency: float  # Logical consistency [0, 1]
    traceability: float  # Cryptographic traceability [0, 1]


class OmegaGate:
    """
    Ω-GATE: Mathematical governance gate for scientific decisions
    Implements: Ω(s,c) = 1 ⟺ [Ψ(s) ≥ Ψ_min] ∧ [Θ̄(s) ≤ Θ_SLA] ∧ [CVaR_α(s) ≤ R_max]
    """

    def __init__(
        self,
        psi_min: float = 0.55,
        theta_sla: float = 0.8,
        cvar_max: float = 0.4,
        alpha_min: float = 1.0
    ):
        self.psi_min = psi_min
        self.theta_sla = theta_sla
        self.cvar_max = cvar_max
        self.alpha_min = alpha_min

    def calculate_psi(self, metrics: GovernanceMetrics) -> float:
        """
        Calculate Ψ-index (Semantic Coherence)
        Ψ = 0.4·Completude + 0.3·Consistência + 0.3·Rastreabilidade
        """
        psi = (
            0.4 * metrics.completeness +
            0.3 * metrics.consistency +
            0.3 * metrics.traceability
        )
        return np.clip(psi, 0, 1)

    def calculate_theta(self, metrics: GovernanceMetrics) -> float:
        """
        Calculate Θ-score (Performance)
        Normalized with exponential decay
        """
        theta_norm = np.exp(-metrics.theta / 0.5)  # τ_ref = 0.5
        return np.clip(theta_norm, 0, 1)

    def calculate_cvar(self, loss_distribution: np.ndarray, alpha: float = 0.95) -> float:
        """
        Calculate CVaR (Conditional Value at Risk)
        CVaR_α = E[L | L ≥ VaR_α]
        """
        var = np.percentile(loss_distribution, alpha * 100)
        tail_losses = loss_distribution[loss_distribution >= var]
        cvar = np.mean(tail_losses) if len(tail_losses) > 0 else 0
        return cvar

    def smooth_decision(self, metrics: GovernanceMetrics, beta: float = 10.0) -> float:
        """
        Smooth decision function using sigmoid
        Ω̃(s,c) = σ(β · Σᵢ wᵢ · δᵢ(s))
        """
        delta_psi = metrics.psi - self.psi_min
        delta_theta = self.theta_sla - metrics.theta
        delta_cvar = self.cvar_max - metrics.cvar
        delta_alpha = metrics.alpha - self.alpha_min

        # Weighted sum
        weighted_sum = (
            0.4 * delta_psi +
            0.3 * delta_theta +
            0.2 * delta_cvar +
            0.1 * delta_alpha
        )

        # Sigmoid activation
        decision_score = 1 / (1 + np.exp(-beta * weighted_sum))
        return decision_score

    def decide(self, metrics: GovernanceMetrics) -> Decision:
        """
        Make binary decision based on governance metrics
        """
        psi = self.calculate_psi(metrics)
        theta = self.calculate_theta(metrics)

        # Binary decision rule
        if (
            psi >= self.psi_min and
            theta <= self.theta_sla and
            metrics.cvar <= self.cvar_max and
            metrics.alpha >= self.alpha_min
        ):
            return Decision.APPROVE
        if psi < self.psi_min * 0.8:
            return Decision.REJECT
        return Decision.REVIEW

    def explain_decision(self, metrics: GovernanceMetrics) -> Dict[str, Any]:
        """
        Generate explanation for decision
        """
        decision = self.decide(metrics)
        smooth_score = self.smooth_decision(metrics)

        explanation = {
            "decision": decision.value,
            "confidence": float(smooth_score),
            "thresholds": {
                "psi_min": self.psi_min,
                "theta_sla": self.theta_sla,
                "cvar_max": self.cvar_max,
                "alpha_min": self.alpha_min
            },
            "metrics": {
                "psi": float(metrics.psi),
                "theta": float(metrics.theta),
                "cvar": float(metrics.cvar),
                "alpha": float(metrics.alpha)
            },
            "passed": {
                "psi": metrics.psi >= self.psi_min,
                "theta": metrics.theta <= self.theta_sla,
                "cvar": metrics.cvar <= self.cvar_max,
                "alpha": metrics.alpha >= self.alpha_min
            }
        }

        return explanation


# Example usage
if __name__ == "__main__":
    # Example metrics
    metrics = GovernanceMetrics(
        psi=0.75,
        theta=0.6,
        cvar=0.3,
        alpha=1.2,
        completeness=0.8,
        consistency=0.7,
        traceability=0.9
    )

    gate = OmegaGate()
    decision = gate.decide(metrics)
    explanation = gate.explain_decision(metrics)

    print(f"Decision: {decision}")
    print(f"Explanation: {explanation}")
