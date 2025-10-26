from agents.sensory_contract import SensoryReport, InteractionResult, AccessibilityResult, PlaywrightResult


def test_sensory_report_warnings_round_trip() -> None:
    report = SensoryReport(
        status="needs_fix",
        alignment_score=0.1,
        spacing_score=0.2,
        contrast_score=0.3,
        visible_sections=["hero"],
        interaction=InteractionResult(details="demo"),
        a11y=AccessibilityResult(violations=0),
        playwright=PlaywrightResult(passed=True, total_tests=0),
        warnings=["Vision fallback used", "Network log unavailable"],
    )

    serialized = report.to_dict()
    assert serialized["warnings"] == ["Vision fallback used", "Network log unavailable"]

    hydrated = SensoryReport.from_dict(serialized)
    assert hydrated.warnings == ["Vision fallback used", "Network log unavailable"]
