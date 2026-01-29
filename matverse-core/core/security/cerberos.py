"""
CERBEROS - Temporal-Contextual Antifraud System
Three-headed guard for scientific sovereignty
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import numpy as np


class CerberosPhase(Enum):
    PAST = "past"      # Historical consistency
    PRESENT = "present" # Behavioral pattern
    FUTURE = "future"   # Contextual legitimacy


@dataclass
class ActionContext:
    """Context for an action to be validated"""
    actor_id: str
    action_type: str
    timestamp: float
    resources: Dict[str, Any]
    previous_actions: List[str]
    environmental_context: Dict[str, Any]
    proposed_changes: Dict[str, Any]


class CerberosHead:
    """Base class for Cerberos validation heads"""

    def __init__(self, phase: CerberosPhase):
        self.phase = phase
        self.history = {}

    def validate(self, context: ActionContext) -> Tuple[bool, str]:
        """Validate action in this phase"""
        raise NotImplementedError


class PastHead(CerberosHead):
    """Validates historical consistency"""

    def __init__(self):
        super().__init__(CerberosPhase.PAST)
        self.action_patterns = {}
        self.consistency_threshold = 0.7

    def validate(self, context: ActionContext) -> Tuple[bool, str]:
        actor = context.actor_id

        # Check action frequency
        now = time.time()
        if actor in self.history:
            last_action_time = self.history[actor].get("last_action", 0)
            time_diff = now - last_action_time

            # Too frequent actions might be automated attacks
            if time_diff < 1.0:  # 1 second minimum between actions
                return False, f"Action too frequent: {time_diff:.2f}s"

        # Update history
        if actor not in self.history:
            self.history[actor] = {
                "first_seen": now,
                "action_count": 0,
                "action_types": set(),
                "last_action": now
            }

        self.history[actor]["action_count"] += 1
        self.history[actor]["action_types"].add(context.action_type)
        self.history[actor]["last_action"] = now

        # Check for radical changes in behavior
        if self._is_behavioral_anomaly(actor, context):
            return False, "Behavioral anomaly detected"

        return True, "Historical consistency validated"

    def _is_behavioral_anomaly(self, actor: str, context: ActionContext) -> bool:
        """Detect if action represents radical behavioral change"""
        if actor not in self.history:
            return False

        history = self.history[actor]

        # If this is a new action type for this actor
        if context.action_type not in history["action_types"]:
            # Check if actor has established pattern
            if history["action_count"] > 10:
                # Established actor trying new action type - flag for review
                return True

        return False


class PresentHead(CerberosHead):
    """Validates present behavioral patterns"""

    def __init__(self, window_size: int = 100):
        super().__init__(CerberosPhase.PRESENT)
        self.window_size = window_size
        self.action_windows = {}

    def validate(self, context: ActionContext) -> Tuple[bool, str]:
        actor = context.actor_id

        # Initialize window for actor
        if actor not in self.action_windows:
            self.action_windows[actor] = deque(maxlen=self.window_size)

        window = self.action_windows[actor]

        # Check for pattern repetition (possible replay attack)
        current_pattern = self._create_action_pattern(context)

        if len(window) >= 3:
            # Check if same pattern repeated recently
            recent_patterns = list(window)[-3:]
            if all(p == current_pattern for p in recent_patterns):
                return False, "Pattern repetition detected"

        # Add to window
        window.append(current_pattern)

        # Check resource access patterns
        if self._is_resource_abuse(context):
            return False, "Resource abuse detected"

        return True, "Behavioral pattern validated"

    def _create_action_pattern(self, context: ActionContext) -> str:
        """Create hash pattern for action"""
        pattern_data = f"{context.action_type}:{context.timestamp}:{len(context.resources)}"
        return hashlib.sha256(pattern_data.encode()).hexdigest()[:16]

    def _is_resource_abuse(self, context: ActionContext) -> bool:
        """Detect resource abuse patterns"""
        # Check for excessive resource requests
        resource_count = len(context.resources)
        if resource_count > 100:  # Arbitrary threshold
            return True

        # Check for suspicious resource combinations
        suspicious_combinations = [
            {"admin", "delete", "all"},
            {"root", "override", "permissions"}
        ]

        action_resources = set(context.resources.keys())
        for combo in suspicious_combinations:
            if combo.issubset(action_resources):
                return True

        return False


class FutureHead(CerberosHead):
    """Validates future contextual legitimacy"""

    def __init__(self):
        super().__init__(CerberosPhase.FUTURE)
        self.scenario_models = {}

    def validate(self, context: ActionContext) -> Tuple[bool, str]:
        # Simulate future impact
        impact_score = self._simulate_impact(context)

        if impact_score > 0.8:  # High negative impact
            return False, f"High negative impact predicted: {impact_score:.2f}"

        # Check for takeover attempts
        if self._is_takeover_attempt(context):
            return False, "Takeover attempt detected"

        # Validate contextual legitimacy
        if not self._is_contextually_legitimate(context):
            return False, "Contextual legitimacy failed"

        return True, "Future context validated"

    def _simulate_impact(self, context: ActionContext) -> float:
        """Simulate potential future impact of action"""
        # Simple simulation - in reality would use ML model
        risk_factors = 0

        # Factor 1: Number of proposed changes
        change_count = len(context.proposed_changes)
        risk_factors += min(change_count / 10, 1.0) * 0.3

        # Factor 2: Critical resource access
        critical_resources = {"admin", "root", "sudo", "delete", "override"}
        critical_access = len(set(context.resources.keys()) & critical_resources)
        risk_factors += min(critical_access / 3, 1.0) * 0.4

        # Factor 3: Rate of change
        if context.actor_id in self.history:
            history = self.history[context.actor_id]
            action_rate = history.get("action_rate", 1.0)
            risk_factors += min(action_rate / 10, 1.0) * 0.3

        return risk_factors

    def _is_takeover_attempt(self, context: ActionContext) -> bool:
        """Detect system takeover attempts"""
        takeover_indicators = [
            "assume_role",
            "elevate_privileges",
            "bypass_authentication",
            "disable_security",
            "override_governance"
        ]

        action_lower = context.action_type.lower()
        for indicator in takeover_indicators:
            if indicator in action_lower:
                return True

        # Check proposed changes for sovereignty violations
        for change in context.proposed_changes.values():
            if isinstance(change, dict):
                if change.get("target") == "governance_core":
                    return True

        return False

    def _is_contextually_legitimate(self, context: ActionContext) -> bool:
        """Check if action is legitimate in current context"""
        # Time-based legitimacy
        hour = time.localtime(context.timestamp).tm_hour
        if hour < 6 or hour > 22:  # Unusual hours
            # Might need additional verification
            pass

        # Resource-context legitimacy
        expected_resources = self._get_expected_resources(context.action_type)
        unexpected = set(context.resources.keys()) - set(expected_resources)

        if len(unexpected) > 2:  # Too many unexpected resources
            return False

        return True

    def _get_expected_resources(self, action_type: str) -> List[str]:
        """Get expected resources for action type"""
        # This would come from a policy database
        resource_map = {
            "publish_paper": ["paper_storage", "doi_service", "metadata_db"],
            "update_profile": ["user_db", "orcid_api"],
            "submit_review": ["review_queue", "paper_db"],
            "request_funding": ["grant_db", "wallet_service"]
        }

        return resource_map.get(action_type, [])


class Cerberos:
    """
    CERBEROS: Three-headed antifraud system
    Validates: Past consistency, Present behavior, Future legitimacy
    """

    def __init__(self):
        self.past_head = PastHead()
        self.present_head = PresentHead()
        self.future_head = FutureHead()
        self.overall_threshold = 0.6  # Minimum combined score

    def validate_action(self, context: ActionContext) -> Dict[str, Any]:
        """
        Validate action through all three heads
        Returns comprehensive validation result
        """
        results = {}
        scores = []

        # Phase 1: Past validation
        past_valid, past_reason = self.past_head.validate(context)
        results["past"] = {
            "valid": past_valid,
            "reason": past_reason,
            "score": 1.0 if past_valid else 0.0
        }
        scores.append(1.0 if past_valid else 0.0)

        # Phase 2: Present validation
        present_valid, present_reason = self.present_head.validate(context)
        results["present"] = {
            "valid": present_valid,
            "reason": present_reason,
            "score": 1.0 if present_valid else 0.0
        }
        scores.append(1.0 if present_valid else 0.0)

        # Phase 3: Future validation
        future_valid, future_reason = self.future_head.validate(context)
        results["future"] = {
            "valid": future_valid,
            "reason": future_reason,
            "score": 1.0 if future_valid else 0.0
        }
        scores.append(1.0 if future_valid else 0.0)

        # Combined decision
        combined_score = np.mean(scores)
        overall_valid = combined_score >= self.overall_threshold

        results["overall"] = {
            "valid": overall_valid,
            "score": float(combined_score),
            "threshold": self.overall_threshold,
            "decision": "APPROVED" if overall_valid else "REJECTED"
        }

        return results

    def learn_from_outcome(
        self,
        context: ActionContext,
        was_correct: bool,
        actual_outcome: Dict[str, Any]
    ):
        """
        Learn from validation outcomes to improve future decisions
        """
        # Update thresholds based on outcomes
        if not was_correct:
            # False positive or false negative
            # Adjust thresholds accordingly
            pass


# Example usage
if __name__ == "__main__":
    cerberos = Cerberos()

    # Example action context
    context = ActionContext(
        actor_id="researcher_001",
        action_type="publish_paper",
        timestamp=time.time(),
        resources={
            "paper_storage": "write",
            "doi_service": "create",
            "metadata_db": "update"
        },
        previous_actions=["write_paper", "submit_draft"],
        environmental_context={
            "ip_address": "192.168.1.100",
            "user_agent": "MatVerse-CLI/1.0",
            "location": "BR"
        },
        proposed_changes={
            "new_paper": {
                "title": "Quantum Semantic Systems",
                "authors": ["Researcher 001"],
                "abstract": "..."
            }
        }
    )

    # Validate action
    result = cerberos.validate_action(context)
    print("CERBEROS Validation Result:")
    print(json.dumps(result, indent=2))
