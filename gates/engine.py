"""Gate Engine - Pluggable quality gate evaluation system.

Evaluates expectations against sensory observations using composable predicates.
This removes hard-coded page semantics from the orchestrator.
"""

from typing import Dict, Any, List, Callable, Tuple, Optional


class GateRegistry:
    """Registry of gate predicates."""
    
    def __init__(self):
        self.predicates: Dict[str, Callable] = {}
        self._register_default_predicates()
    
    def register(self, name: str, predicate: Callable[[Dict, Dict], Tuple[bool, str]]):
        """Register a new predicate.
        
        Args:
            name: Predicate name
            predicate: Function taking (expectations, observations) returning (passed, reason)
        """
        self.predicates[name] = predicate
    
    def _register_default_predicates(self):
        """Register built-in predicates."""

        self.register("kpi_min", self._kpi_min)
        self.register("charts_min", self._charts_min)
        self.register("tables_min", self._tables_min)
        self.register("filters_required", self._filters_required)
        self.register("form_submit_ok", self._form_submit_ok)
        self.register("alignment_score", self._alignment_score)
        self.register("spacing_score", self._spacing_score)
        self.register("contrast_score", self._contrast_score)

    def _get_capability_config(self, expectations: Dict, key: str) -> Dict[str, Any]:
        """Normalize capability expectation values to a dictionary."""

        capabilities = expectations.get("capabilities", {})
        value = capabilities.get(key, {})

        if isinstance(value, dict):
            return value

        if isinstance(value, bool):
            # Treat booleans as a simple required flag.
            return {"required": value}

        if isinstance(value, (int, float)):
            # Numeric capabilities map to a minimum requirement.
            return {"min": value}

        return {}

    def _kpi_min(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check minimum KPI tiles count."""
        required = self._get_capability_config(expectations, "kpi_tiles").get("min", 0)
        if required == 0:
            return True, ""

        actual = observations.get("elements", {}).get("kpi_tiles", 0)
        if actual >= required:
            return True, ""
        return False, f"kpi_tiles: expected >={required}, got {actual}"
    
    def _charts_min(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check minimum charts count."""
        required = self._get_capability_config(expectations, "charts").get("min", 0)
        if required == 0:
            return True, ""

        actual = observations.get("elements", {}).get("charts", 0)
        if actual >= required:
            return True, ""
        return False, f"charts: expected >={required}, got {actual}"
    
    def _tables_min(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check minimum tables count."""
        required = self._get_capability_config(expectations, "tables").get("min", 0)
        if required == 0:
            return True, ""

        actual = observations.get("elements", {}).get("tables", 0)
        if actual >= required:
            return True, ""
        return False, f"tables: expected >={required}, got {actual}"

    def _filters_required(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check if filters are present when required."""
        config = self._get_capability_config(expectations, "filters")
        required = config.get("required", False)
        if not required:
            return True, ""

        actual = observations.get("elements", {}).get("filters", 0)
        if actual > 0:
            return True, ""
        return False, "filters: required but not found"
    
    def _form_submit_ok(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check form submission success."""
        interactions_expected = expectations.get("interactions", [])
        if not interactions_expected:
            return True, ""
        
        interactions_actual = observations.get("interactions", {})
        
        failures = []
        for interaction in interactions_expected:
            if interaction["type"] != "form_submit":
                continue
            
            interaction_id = interaction["id"]
            actual = interactions_actual.get(interaction_id, {})
            
            if not actual.get("attempted", False):
                failures.append(f"{interaction_id}: not attempted")
                continue
            
            if interaction.get("expect_http_2xx", False):
                status = actual.get("http_status")
                if status is None:
                    failures.append(f"{interaction_id}: http_status not captured")
                    continue
                if not (200 <= status < 300):
                    failures.append(f"{interaction_id}: http_status {status} not 2xx")
            
            if interaction.get("expect_success_banner", False):
                if not actual.get("success_banner", False):
                    failures.append(f"{interaction_id}: success_banner not shown")
            
            if actual.get("error_banner", False):
                failures.append(f"{interaction_id}: error_banner shown")
        
        if failures:
            return False, "; ".join(failures)
        return True, ""
    
    def _alignment_score(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check alignment score threshold."""
        threshold = expectations.get("thresholds", {}).get("alignment_score", 0.90)
        actual = observations.get("vision_scores", {}).get("alignment", 0.0)
        
        if actual >= threshold:
            return True, ""
        return False, f"alignment_score: {actual:.2f} < {threshold:.2f}"
    
    def _spacing_score(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check spacing score threshold."""
        threshold = expectations.get("thresholds", {}).get("spacing_score", 0.90)
        actual = observations.get("vision_scores", {}).get("spacing", 0.0)
        
        if actual >= threshold:
            return True, ""
        return False, f"spacing_score: {actual:.2f} < {threshold:.2f}"
    
    def _contrast_score(self, expectations: Dict, observations: Dict) -> Tuple[bool, str]:
        """Check contrast score threshold."""
        threshold = expectations.get("thresholds", {}).get("contrast_score", 0.75)
        actual = observations.get("vision_scores", {}).get("contrast", 0.0)
        
        if actual >= threshold:
            return True, ""
        return False, f"contrast_score: {actual:.2f} < {threshold:.2f}"


_default_registry = GateRegistry()


def evaluate(
    expectations: Dict[str, Any],
    observations: Dict[str, Any],
    registry: Optional[GateRegistry] = None
) -> Dict[str, Any]:
    """Evaluate all gates and return verdict.
    
    Args:
        expectations: Expected capabilities and interactions
        observations: Actual observations from sensory agent
        registry: Custom predicate registry (uses default if None)
        
    Returns:
        Dictionary with passed (bool) and failing_reasons (list)
    """
    if registry is None:
        registry = _default_registry
    
    if "thresholds" not in expectations:
        expectations["thresholds"] = {
            "alignment_score": 0.90,
            "spacing_score": 0.90,
            "contrast_score": 0.75
        }
    
    failing_reasons = []
    
    for predicate_name, predicate_func in registry.predicates.items():
        passed, reason = predicate_func(expectations, observations)
        if not passed and reason:
            failing_reasons.append(reason)
    
    return {
        "passed": len(failing_reasons) == 0,
        "failing_reasons": failing_reasons
    }


def get_fix_instructions(
    expectations: Dict[str, Any],
    observations: Dict[str, Any],
    failing_reasons: List[str]
) -> str:
    """Generate targeted fix instructions from gate failures.
    
    Args:
        expectations: Expected capabilities and interactions
        observations: Actual observations
        failing_reasons: List of failing gate reasons
        
    Returns:
        Markdown-formatted fix instructions
    """
    if not failing_reasons:
        return "All quality gates passed. No fixes needed."
    
    instructions = ["## Required Fixes\n"]
    
    for reason in failing_reasons:
        if "alignment_score" in reason:
            instructions.append(
                "### Layout Alignment\n"
                "- Improve CSS grid/flexbox alignment\n"
                "- Ensure consistent element positioning\n"
                "- Fix any visual misalignments\n"
            )
        
        elif "spacing_score" in reason:
            instructions.append(
                "### Spacing and Typography\n"
                "- Apply consistent spacing scale (8px, 16px, 24px, etc.)\n"
                "- Improve margin/padding consistency\n"
                "- Enhance typography hierarchy\n"
            )
        
        elif "contrast_score" in reason:
            instructions.append(
                "### Contrast and Readability\n"
                "- Increase text contrast ratios\n"
                "- Use darker text on light backgrounds\n"
                "- Ensure WCAG AA compliance\n"
            )
        
        elif "kpi_tiles" in reason or "charts" in reason or "tables" in reason or "filters" in reason:
            instructions.append(
                f"### Missing Component\n"
                f"- {reason}\n"
                f"- Add required UI elements to meet expectations\n"
            )
        
        elif any(interaction_id in reason for interaction_id in ["contact_submit", "newsletter_signup", "login_form"]):
            interaction_id = reason.split(":")[0]
            instructions.append(
                f"### {interaction_id} Interaction Failure\n"
                f"- {reason}\n"
                f"- Fix JavaScript form submission handler\n"
                f"- Ensure backend route processes POST requests correctly\n"
                f"- Display appropriate success/error messages\n"
            )
    
    return "\n".join(instructions)
