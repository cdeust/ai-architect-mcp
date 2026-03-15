"""HOR Rule Engine — registration, execution, and score adjustment.

Auto-discovers rules from category modules. Runs all 64 rules
against an artifact and calculates score penalties. Async methods
support optional observability event emission.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_architect_mcp._models.verification import (
    PENALTY_CRITICAL,
    PENALTY_WARNING,
    HORRuleResult,
    HORSeverity,
)

RuleFunction = Callable[[dict[str, Any]], HORRuleResult]


class HORRuleEngine:
    """Engine for registering and executing HOR rules.

    Auto-discovers rules from category modules during initialization.
    Provides async methods to run rules with optional observability.
    """

    def __init__(self, observability: Any | None = None) -> None:
        """Initialize the HOR rule engine and register all rules.

        Args:
            observability: Optional ObservabilityPort for event emission.
        """
        self._rules: dict[int, tuple[RuleFunction, str, str, HORSeverity]] = {}
        self._observability = observability
        self._auto_discover()

    def register(
        self,
        rule_id: int,
        rule_fn: RuleFunction,
        category: str,
        name: str,
        severity: HORSeverity,
    ) -> None:
        """Register a rule with the engine.

        Args:
            rule_id: Unique rule identifier (1-64).
            rule_fn: The rule function to execute.
            category: Category grouping.
            name: Human-readable rule name.
            severity: Rule severity level.
        """
        self._rules[rule_id] = (rule_fn, category, name, severity)

    async def run_all(self, artifact: dict[str, Any]) -> list[HORRuleResult]:
        """Run all registered rules against an artifact.

        Args:
            artifact: The artifact to verify.

        Returns:
            List of HORRuleResult for all 64 rules.
        """
        results: list[HORRuleResult] = []
        for rule_id in sorted(self._rules.keys()):
            results.append(await self.run_single(rule_id, artifact))
        return results

    async def run_by_category(
        self, category: str, artifact: dict[str, Any]
    ) -> list[HORRuleResult]:
        """Run all rules in a specific category.

        Args:
            category: The category to run.
            artifact: The artifact to verify.

        Returns:
            List of HORRuleResult for rules in the category.
        """
        results: list[HORRuleResult] = []
        for rule_id in sorted(self._rules.keys()):
            _, cat, _, _ = self._rules[rule_id]
            if cat == category:
                results.append(await self.run_single(rule_id, artifact))
        return results

    async def run_single(
        self, rule_id: int, artifact: dict[str, Any]
    ) -> HORRuleResult:
        """Run a single rule by ID.

        Args:
            rule_id: The rule ID to execute.
            artifact: The artifact to verify.

        Returns:
            The HORRuleResult from the rule.

        Raises:
            KeyError: If rule_id is not registered.
        """
        if rule_id not in self._rules:
            msg = (
                f"Rule {rule_id} is not registered"
                f" — available rules: {sorted(self._rules.keys())}"
            )
            raise KeyError(msg)
        rule_fn, category, name, _ = self._rules[rule_id]
        result = rule_fn(artifact)

        if self._observability is not None:
            from ai_architect_mcp._observability.instrumentation import (
                emit_hor_rule,
            )
            await emit_hor_rule(
                rule_id=rule_id,
                rule_name=name,
                category=category,
                passed=result.passed,
            )
        return result

    def calculate_adjusted_score(
        self, base_score: float, results: list[HORRuleResult]
    ) -> float:
        """Calculate score after applying HOR rule penalties.

        Critical failures: -0.15 per failure.
        Warning failures: -0.05 per failure.

        Args:
            base_score: The starting score before penalties.
            results: List of HORRuleResult to check for failures.

        Returns:
            Adjusted score clamped to [0.0, base_score].
        """
        total_penalty = 0.0
        for result in results:
            if not result.passed:
                total_penalty += result.penalty
        return max(0.0, base_score - total_penalty)

    @property
    def rule_count(self) -> int:
        """Return the number of registered rules."""
        return len(self._rules)

    def _auto_discover(self) -> None:
        """Auto-discover and register rules from category modules."""
        from ai_architect_mcp._verification.hor_rules.architecture import (
            get_rules as arch_rules,
        )
        from ai_architect_mcp._verification.hor_rules.observability import (
            get_rules as obs_rules,
        )
        from ai_architect_mcp._verification.hor_rules.quality import (
            get_rules as qual_rules,
        )
        from ai_architect_mcp._verification.hor_rules.resilience import (
            get_rules as res_rules,
        )
        from ai_architect_mcp._verification.hor_rules.security import (
            get_rules as sec_rules,
        )
        from ai_architect_mcp._verification.hor_rules.structural import (
            get_rules as struct_rules,
        )
        from ai_architect_mcp._verification.hor_rules.structural_extended import (
            get_rules as struct_ext_rules,
        )

        for module_rules in [
            struct_rules,
            struct_ext_rules,
            arch_rules,
            sec_rules,
            res_rules,
            qual_rules,
            obs_rules,
        ]:
            for rule_id, rule_fn, category, name, severity in module_rules():
                self.register(rule_id, rule_fn, category, name, severity)
