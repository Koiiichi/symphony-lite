# API Contract - Sensory ⇄ Brain Communication

## Overview

Symphony-Lite uses a standardized JSON contract between the Sensory and Brain agents to ensure consistent, actionable feedback for targeted fixes.

## SensoryReport Format

### Top-Level Structure

```json
{
  "status": "pass" | "needs_fix",
  "alignment_score": 0.0-1.0,
  "spacing_score": 0.0-1.0,
  "contrast_score": 0.0-1.0,
  "visible_sections": ["hero", "projects", "contact", ...],
  "interaction": { InteractionResult },
  "a11y": { AccessibilityResult },
  "playwright": { PlaywrightResult },
  "screens": [ Screenshot, ... ]
}
```

### InteractionResult

```json
{
  "contact_submitted": true | false,
  "details": "Description of what happened",
  "errors": ["Error message 1", "Error message 2", ...]
}
```

### AccessibilityResult

```json
{
  "violations": 0,
  "top_issues": [
    "Button missing accessible label",
    "Low contrast ratio on muted text",
    ...
  ],
  "wcag_level": "AA"
}
```

### PlaywrightResult

```json
{
  "passed": true | false,
  "failed_tests": ["Test name 1", "Test name 2", ...],
  "total_tests": 0
}
```

### Screenshot

```json
{
  "page": "initial_load" | "after_scroll" | "after_submit",
  "path": "artifacts/run_20251013_143022/step_1_initial.png",
  "timestamp": "2025-10-13T14:30:22Z"
}
```

## Quality Gates

### Default Thresholds

```python
{
    "alignment_score": 0.90,
    "spacing_score": 0.90,
    "contrast_score": 0.75,
    "a11y_violations": 5
}
```

### Pass Criteria

A run passes all quality gates when:

1. `status == "pass"`
2. `alignment_score >= 0.90`
3. `spacing_score >= 0.90`
4. `contrast_score >= 0.75` (more lenient for dark themes)
5. `interaction.contact_submitted == true` (if contact form exists)
6. `a11y.violations <= 5`
7. `playwright.passed == true` (if tests exist)

## Brain Fix Policy

The Brain agent receives targeted fix instructions based on failing gates:

### Alignment Score < 0.90

```markdown
### Layout Alignment
- Improve CSS grid/flexbox alignment
- Ensure consistent element positioning
- Fix any visual misalignments
```

**Root causes**:
- Elements not properly centered
- Inconsistent grid/flex configurations
- Missing or incorrect positioning properties

### Spacing Score < 0.90

```markdown
### Spacing and Typography
- Apply consistent spacing scale (8px, 16px, 24px, etc.)
- Improve margin/padding consistency
- Enhance typography hierarchy
```

**Root causes**:
- Random margin/padding values
- Inconsistent whitespace
- Poor visual rhythm

### Contrast Score < 0.75

```markdown
### Contrast and Readability
- Increase text contrast ratios
- Use darker text on light backgrounds
- Ensure WCAG AA compliance
```

**Root causes**:
- Low contrast text colors
- Insufficient color differentiation
- Accessibility violations

### Contact Form Not Working

```markdown
### Contact Form Functionality
- Fix JavaScript form submission handler
- Ensure backend route processes POST requests
- Display success/error messages to user
- Details: {specific error from interaction.details}
```

**Root causes**:
- Missing event listener
- Incorrect API endpoint
- Backend not handling POST
- Missing error handling

### Accessibility Violations > 5

```markdown
### Accessibility Issues ({violations} violations)
- {top_issue_1}
- {top_issue_2}
- {top_issue_3}
```

**Root causes**:
- Missing ARIA labels
- Form inputs without labels
- Images without alt text
- Low contrast text

### Playwright Tests Failing

```markdown
### Test Failures
- Fix: {failed_test_1}
- Fix: {failed_test_2}
- Fix: {failed_test_3}
```

**Root causes**:
- Broken functionality
- Incorrect selectors
- Missing elements
- Timing issues

## Example Complete Report

```json
{
  "status": "needs_fix",
  "alignment_score": 0.85,
  "spacing_score": 0.92,
  "contrast_score": 0.78,
  "visible_sections": ["hero", "projects", "contact"],
  "interaction": {
    "contact_submitted": false,
    "details": "Could not find submit button",
    "errors": ["Could not find or click submit button"]
  },
  "a11y": {
    "violations": 3,
    "top_issues": [
      "Button missing accessible label",
      "Low contrast ratio (3.2:1) on muted text",
      "Form input missing associated label"
    ],
    "wcag_level": "AA"
  },
  "playwright": {
    "passed": true,
    "failed_tests": [],
    "total_tests": 0
  },
  "screens": [
    {
      "page": "initial_load",
      "path": "artifacts/run_20251013_143022/step_1_initial.png"
    },
    {
      "page": "after_scroll",
      "path": "artifacts/run_20251013_143022/step_2_scroll.png"
    },
    {
      "page": "after_submit",
      "path": "artifacts/run_20251013_143022/step_3_submit.png"
    }
  ]
}
```

### Failing Gates

From the above report:
- `alignment_score (0.85 < 0.90)`
- `contact_form_not_working`
- `a11y_violations (3 > threshold of 5)` - Actually passing!

### Generated Fix Instructions

```markdown
## Required Fixes

### Layout Alignment
- Improve CSS grid/flexbox alignment
- Ensure consistent element positioning
- Fix any visual misalignments

### Contact Form Functionality
- Fix JavaScript form submission handler
- Ensure backend route processes POST requests
- Display success/error messages to user
- Details: Could not find submit button
```

## Python API

### Creating a Report

```python
from agents.sensory_contract import (
    SensoryReport,
    InteractionResult,
    AccessibilityResult,
    Screenshot
)

report = SensoryReport(
    status="pass",
    alignment_score=0.92,
    spacing_score=0.95,
    contrast_score=0.88,
    visible_sections=["hero", "projects", "contact"],
    interaction=InteractionResult(
        contact_submitted=True,
        details="Form submitted successfully"
    ),
    a11y=AccessibilityResult(
        violations=2,
        top_issues=["Image missing alt text"]
    ),
    screens=[
        Screenshot(page="initial", path="artifacts/run_123/step_1.png")
    ]
)
```

### Checking Gates

```python
# Check if all gates pass
if report.passes_all_gates():
    print("Success!")

# Get list of failing gates
failing = report.get_failing_gates()
# Returns: ["alignment_score (0.85 < 0.90)", "contact_form_not_working"]

# Get targeted fix instructions
instructions = report.get_fix_instructions()
# Returns markdown-formatted instructions
```

### Serialization

```python
# To dictionary
data = report.to_dict()

# To JSON string
json_str = report.to_json()

# From dictionary
report = SensoryReport.from_dict(data)
```

## Custom Thresholds

You can customize quality gate thresholds:

```python
custom_thresholds = {
    "alignment_score": 0.95,  # Stricter
    "spacing_score": 0.85,    # More lenient
    "contrast_score": 0.80,   # Higher for light themes
    "a11y_violations": 0      # Zero tolerance
}

failing_gates = report.get_failing_gates(custom_thresholds)
passes = report.passes_all_gates(custom_thresholds)
```

## Integration with Brain Agent

The Brain agent receives the full SensoryReport and uses it to make targeted fixes:

1. **Parse failing gates**: Identify which quality metrics need improvement
2. **Generate instructions**: Use `get_fix_instructions()` for markdown template
3. **Read existing code**: Examine files likely to need fixes
4. **Apply targeted changes**: Update only what's needed
5. **Preserve functionality**: Don't break working features

## Artifacts

All screenshots and artifacts are organized by `run_id`:

```
artifacts/
  run_20251013_143022/
    step_1_initial_1697218222.png
    step_2_scroll_1697218224.png
    step_3_submit_1697218227.png
```

This prevents conflicts when running multiple workflows concurrently.
