from __future__ import annotations

import re
from typing import List

from .types import IntentResult, StackInfo


_UI_KEYWORDS = {
    "ui", "ux", "design", "spacing", "alignment", "contrast", "accessibility",
    "responsive", "layout", "typography", "visual", "style", "padding",
}

_REFINE_KEYWORDS = {
    "refine", "improve", "fix", "tweak", "polish", "optimize", "enhance", "update",
    "adjust", "repair", "upgrade", "cleanup", "clean up", "bug", "issue", "regression",
}

_CREATE_KEYWORDS = {
    "create", "build", "scaffold", "generate", "start", "new", "from scratch",
}

_TOPIC_KEYWORDS = {
    "ui_ux": _UI_KEYWORDS,
    "bug": {"bug", "fix", "error", "regression", "broken", "fail"},
    "feature": {"add", "implement", "support", "feature", "integrate"},
    "infra": {"deploy", "pipeline", "ci", "infrastructure", "build system", "docker"},
    "data_pipeline": {"etl", "ingest", "data", "pipeline", "warehouse", "analytics"},
}


def _contains_any(text: str, keywords: List[str] | set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def classify_intent(goal: str, stack: StackInfo) -> IntentResult:
    """Classify user goal into intent/topic buckets using heuristics."""

    lowered = goal.lower()
    reasons: List[str] = []

    has_code = stack.has_code
    mentioned_new = _contains_any(lowered, _CREATE_KEYWORDS)
    mentioned_refine = _contains_any(lowered, _REFINE_KEYWORDS)

    if not has_code and not mentioned_refine:
        intent = "create"
        reasons.append("Project appears empty")
    elif mentioned_new and not mentioned_refine:
        intent = "create"
        reasons.append("Prompt mentions creation")
    else:
        intent = "refine"
        if mentioned_refine:
            reasons.append("Prompt includes refinement language")
        if has_code:
            reasons.append("Existing project detected")

    topic = "feature"
    for topic_name, keywords in _TOPIC_KEYWORDS.items():
        if _contains_any(lowered, keywords):
            topic = topic_name
            reasons.append(f"Matched {topic_name} keywords")
            break

    if topic != "ui_ux" and intent == "refine" and not mentioned_refine and has_code:
        # When prompt is ambiguous but only mentions improvement, favor UI/UX.
        if re.search(r"ui|ux|design|spacing|contrast", lowered):
            topic = "ui_ux"
            reasons.append("Detected UI/UX phrasing")

    if topic == "feature" and intent == "refine" and _contains_any(lowered, _UI_KEYWORDS):
        topic = "ui_ux"
        reasons.append("UI keyword override")

    if topic == "feature" and _contains_any(lowered, {"bug", "issue", "fix"}):
        topic = "bug"
        reasons.append("Bug keyword override")

    confidence = 0.6
    if intent == "create" and mentioned_new:
        confidence = 0.85
    elif intent == "refine" and mentioned_refine:
        confidence = 0.85
    elif intent == "refine" and has_code:
        confidence = 0.7

    if topic == "ui_ux" and _contains_any(lowered, _UI_KEYWORDS):
        confidence = max(confidence, 0.8)

    return IntentResult(intent=intent, topic=topic, confidence=confidence, reasons=reasons)
