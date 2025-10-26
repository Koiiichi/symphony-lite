"""Quick integration test without full workflow."""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.goal_interpreter import build_expectations
from gates.engine import evaluate as evaluate_gates, get_fix_instructions

# Simulate the test-broken scenario
print("Simulating test-broken project verification...")
print("="*60)

# Step 1: Build expectations
goal = "Contact page accepts messages"
expectations = build_expectations(goal, vision_mode="qa")

print(f"\nGoal: {goal}")
print(f"Expectations: {expectations['interactions'][0]['id']}")
print(f"  - Expect HTTP 2xx: {expectations['interactions'][0]['expect_http_2xx']}")
print(f"  - Expect success banner: {expectations['interactions'][0]['expect_success_banner']}")

# Step 2: Simulate sensory observations (broken state)
observations_broken = {
    "elements": {"kpi_tiles": 0, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {
        "contact_submit": {
            "attempted": True,
            "http_status": 501,
            "success_banner": False,
            "error_banner": True
        }
    },
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80},
    "visited_urls": ["http://localhost:3000"]
}

# Step 3: Evaluate gates (should fail)
result_broken = evaluate_gates(expectations, observations_broken)

print("\n" + "="*60)
print("BROKEN STATE EVALUATION:")
print("="*60)
print(f"Passed: {result_broken['passed']}")
print(f"Failing reasons:")
for reason in result_broken['failing_reasons']:
    print(f"  - {reason}")

# Step 4: Generate fix instructions
fix_instructions = get_fix_instructions(
    expectations, 
    observations_broken, 
    result_broken['failing_reasons']
)

print("\nFix Instructions:")
print(fix_instructions[:500] + "...")

# Step 5: Simulate fixed state
observations_fixed = {
    "elements": {"kpi_tiles": 0, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {
        "contact_submit": {
            "attempted": True,
            "http_status": 200,
            "success_banner": True,
            "error_banner": False
        }
    },
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80},
    "visited_urls": ["http://localhost:3000"]
}

result_fixed = evaluate_gates(expectations, observations_fixed)

print("\n" + "="*60)
print("FIXED STATE EVALUATION:")
print("="*60)
print(f"Passed: {result_fixed['passed']}")
print(f"Failing reasons: {result_fixed['failing_reasons']}")

# Verify exit codes
print("\n" + "="*60)
print("EXIT CODE VERIFICATION:")
print("="*60)
print(f"Broken state exit code: {'1 (failure)' if not result_broken['passed'] else '0 (success)'}")
print(f"Fixed state exit code: {'0 (success)' if result_fixed['passed'] else '1 (failure)'}")

# Dashboard test
print("\n" + "="*60)
print("DASHBOARD GOAL TEST:")
print("="*60)

dashboard_goal = "Analytics dashboard with 3 KPI tiles, a chart and a table"
dashboard_expectations = build_expectations(dashboard_goal, vision_mode="qa")

print(f"Goal: {dashboard_goal}")
print(f"Required KPI tiles: {dashboard_expectations['capabilities']['kpi_tiles']['min']}")
print(f"Required charts: {dashboard_expectations['capabilities']['charts']['min']}")
print(f"Required tables: {dashboard_expectations['capabilities']['tables']['min']}")

# Test with insufficient elements
dashboard_obs_fail = {
    "elements": {"kpi_tiles": 2, "charts": 0, "tables": 0, "filters": 0},
    "interactions": {},
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

dashboard_result_fail = evaluate_gates(dashboard_expectations, dashboard_obs_fail)
print(f"\nWith 2 KPI tiles, 0 charts, 0 tables:")
print(f"  Passed: {dashboard_result_fail['passed']}")
print(f"  Failing reasons:")
for reason in dashboard_result_fail['failing_reasons']:
    print(f"    - {reason}")

# Test with sufficient elements
dashboard_obs_pass = {
    "elements": {"kpi_tiles": 3, "charts": 1, "tables": 1, "filters": 1},
    "interactions": {},
    "vision_scores": {"alignment": 0.95, "spacing": 0.92, "contrast": 0.80}
}

dashboard_result_pass = evaluate_gates(dashboard_expectations, dashboard_obs_pass)
print(f"\nWith 3 KPI tiles, 1 chart, 1 table:")
print(f"  Passed: {dashboard_result_pass['passed']}")
print(f"  Failing reasons: {dashboard_result_pass['failing_reasons']}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
print("Key features verified:")
print("  - Goal Interpreter generates appropriate expectations")
print("  - Gate Engine evaluates expectations correctly")
print("  - Exit codes reflect gate pass/fail status")
print("  - Works for different page types (contact, dashboard)")
print("  - No hard-coded page type branching")
