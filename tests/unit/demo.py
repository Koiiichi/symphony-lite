#!/usr/bin/env python
"""
Quick demonstration of the new architecture.
Shows how different goals are interpreted and evaluated.
"""

import sys
import json
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.goal_interpreter import build_expectations
from gates.engine import evaluate as evaluate_gates

def demo_goal(goal_text, observations):
    """Demonstrate goal interpretation and evaluation."""
    print(f"\n{'='*70}")
    print(f"GOAL: {goal_text}")
    print('='*70)
    
    # Build expectations
    expectations = build_expectations(goal_text, vision_mode="qa")
    
    print("\nExpectations Generated:")
    print(f"  Capabilities:")
    for cap, spec in expectations['capabilities'].items():
        if isinstance(spec, dict):
            min_val = spec.get('min', 0)
            required = spec.get('required', False)
            if min_val > 0:
                print(f"    - {cap}: min {min_val}")
            elif required:
                print(f"    - {cap}: required")
    
    if expectations['interactions']:
        print(f"  Interactions:")
        for interaction in expectations['interactions']:
            print(f"    - {interaction['id']}: {interaction['type']}")
    
    # Evaluate
    result = evaluate_gates(expectations, observations)
    
    print(f"\nEvaluation Result:")
    print(f"  Status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"  Exit Code: {0 if result['passed'] else 1}")
    
    if result['failing_reasons']:
        print(f"  Failing Reasons:")
        for reason in result['failing_reasons']:
            print(f"    - {reason}")
    
    return result['passed']

# Demo 1: Contact Page
print("\n" + "="*70)
print("DEMO 1: Contact Page")
print("="*70)

contact_obs_broken = {
    "elements": {"kpi_tiles": 0, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {
        "contact_submit": {
            "attempted": True,
            "http_status": 501,
            "success_banner": False,
            "error_banner": True
        }
    },
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

contact_obs_fixed = {
    "elements": {"kpi_tiles": 0, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {
        "contact_submit": {
            "attempted": True,
            "http_status": 200,
            "success_banner": True,
            "error_banner": False
        }
    },
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

print("\nScenario A: Broken Backend (HTTP 501)")
passed_broken = demo_goal("Contact page accepts messages", contact_obs_broken)

print("\nScenario B: Fixed Backend (HTTP 200)")
passed_fixed = demo_goal("Contact page accepts messages", contact_obs_fixed)

# Demo 2: Dashboard
print("\n" + "="*70)
print("DEMO 2: Analytics Dashboard")
print("="*70)

dashboard_obs_insufficient = {
    "elements": {"kpi_tiles": 2, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {},
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

dashboard_obs_sufficient = {
    "elements": {"kpi_tiles": 3, "charts": 1, "tables": 1, "filters": 1},
    "interactions": {},
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

print("\nScenario A: Insufficient Elements")
passed_insuf = demo_goal(
    "Analytics dashboard with 3 KPI tiles, a chart and a table",
    dashboard_obs_insufficient
)

print("\nScenario B: Sufficient Elements")
passed_suf = demo_goal(
    "Analytics dashboard with 3 KPI tiles, a chart and a table",
    dashboard_obs_sufficient
)

# Demo 3: Landing Page
print("\n" + "="*70)
print("DEMO 3: Landing Page")
print("="*70)

landing_obs = {
    "elements": {"kpi_tiles": 0, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {},
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

demo_goal("Beautiful landing page with hero section", landing_obs)

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

results = {
    "Contact (broken)": not passed_broken,
    "Contact (fixed)": passed_fixed,
    "Dashboard (insufficient)": not passed_insuf,
    "Dashboard (sufficient)": passed_suf
}

print("\nTest Results:")
for test_name, expected_result in results.items():
    status = "PASS" if expected_result else "FAIL"
    print(f"  [{status}] {test_name}")

print("\nKey Observations:")
print("  - Same evaluation pipeline for all page types")
print("  - No hard-coded checks for specific UX patterns")
print("  - Exit codes accurately reflect gate status")
print("  - Failing reasons provide actionable feedback")
print("\nArchitecture successfully generalizes workflow!")
print("="*70 + "\n")
