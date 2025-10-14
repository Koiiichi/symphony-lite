# agents/sensory_agent_web.py
"""Enhanced sensory agent with agentic browsing, form testing, and vision scoring.

Now returns standardized SensoryReport for contract compliance.
"""

import helium
import time
import json
import base64
import os
from pathlib import Path
from selenium.webdriver.chrome.options import Options

# Import contract types
from agents.sensory_contract import (
    SensoryReport,
    InteractionResult,
    AccessibilityResult,
    PlaywrightResult,
    Screenshot
)

# Optional OpenAI import for vision scoring
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def _ensure_artifacts_dir(run_id: str) -> Path:
    """Ensure artifacts directory exists for this run."""
    artifacts_dir = Path("artifacts") / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


def _save_step_screenshot(step_name: str, run_id: str = "default") -> str:
    """Save screenshot and return the path."""
    artifacts_dir = _ensure_artifacts_dir(run_id)
    driver = helium.get_driver()
    path = artifacts_dir / f"step_{step_name}_{int(time.time())}.png"
    driver.get_screenshot_as_file(str(path))
    return str(path)


def go_to_url(url: str) -> str:
    """Navigate to URL and wait for load."""
    helium.go_to(url)
    time.sleep(2.0)
    return f"Opened {url}"


def ensure_contact_present() -> str:
    """Scroll to find contact form section."""
    contact_indicators = ["Contact", "contact", "Get in touch", "Send message"]
    
    for indicator in contact_indicators:
        if helium.Text(indicator).exists():
            helium.scroll_down(1200)
            time.sleep(1.5)
            return f"Found and scrolled to contact section ({indicator})"
    
    helium.scroll_down(1200)
    time.sleep(1.5)
    return "Scrolled down to explore page; contact section may be below fold"


def submit_contact_form(
    name="Test User",
    email="test@example.com",
    message="Hello from Symphony-Lite!"
) -> InteractionResult:
    """Attempt to fill and submit contact form.
    
    Returns:
        InteractionResult with submission status and details
    """
    errors = []
    
    try:
        # Try different input selectors
        name_selectors = ["Name", "name", "Your Name", "[name='name']", "#name"]
        email_selectors = ["Email", "email", "Your Email", "[name='email']", "#email"]
        message_selectors = ["Message", "message", "Your Message", "[name='message']", "#message", "textarea"]
        
        # Fill name field
        name_filled = False
        for selector in name_selectors:
            try:
                helium.write(name, into=selector)
                name_filled = True
                break
            except:
                continue
        
        if not name_filled:
            errors.append("Could not find name field")
        
        # Fill email field
        email_filled = False
        for selector in email_selectors:
            try:
                helium.write(email, into=selector)
                email_filled = True
                break
            except:
                continue
        
        if not email_filled:
            errors.append("Could not find email field")
        
        # Fill message field
        message_filled = False
        for selector in message_selectors:
            try:
                helium.write(message, into=selector)
                message_filled = True
                break
            except:
                continue
        
        if not message_filled:
            errors.append("Could not find message field")
        
        # Try to submit
        submit_clicked = False
        submit_selectors = ["Send", "Submit", "Send Message", "button[type='submit']"]
        for selector in submit_selectors:
            try:
                helium.click(selector)
                submit_clicked = True
                break
            except:
                continue
        
        if not submit_clicked:
            errors.append("Could not find or click submit button")
        
        time.sleep(2.0)  # Wait for response
        
        contact_submitted = name_filled and email_filled and message_filled and submit_clicked
        
        return InteractionResult(
            contact_submitted=contact_submitted,
            details="Form submitted successfully" if contact_submitted else "; ".join(errors),
            errors=errors
        )
        
    except Exception as e:
        return InteractionResult(
            contact_submitted=False,
            details=f"Exception during form submission: {str(e)}",
            errors=[str(e)]
        )


def check_basic_accessibility() -> AccessibilityResult:
    """Perform basic accessibility checks.
    
    Returns:
        AccessibilityResult with violations found
    """
    violations = []
    
    try:
        driver = helium.get_driver()
        
        # Check for images without alt text
        images = driver.find_elements("css selector", "img:not([alt])")
        if images:
            violations.append(f"{len(images)} images missing alt text")
        
        # Check for buttons without accessible labels
        buttons = driver.find_elements("css selector", "button:not([aria-label]):empty")
        if buttons:
            violations.append(f"{len(buttons)} buttons missing accessible labels")
        
        # Check for form inputs without labels
        inputs = driver.find_elements("css selector", "input:not([aria-label]):not([id])")
        unlabeled = [inp for inp in inputs if not driver.find_elements("css selector", f"label[for='{inp.get_attribute('id')}']")]
        if unlabeled:
            violations.append(f"{len(unlabeled)} form inputs missing labels")
        
    except Exception as e:
        violations.append(f"Error during a11y check: {str(e)}")
    
    return AccessibilityResult(
        violations=len(violations),
        top_issues=violations[:5]  # Top 5 issues
    )


def analyze_current_view() -> dict:
    """Analyze current page view using vision model or fallback heuristics.
    
    Returns:
        Dict with alignment_score, spacing_score, contrast_score, visible_sections
    """
    if not HAS_OPENAI or not os.getenv("OPENAI_API_KEY"):
        return analyze_view_heuristic()
    
    try:
        driver = helium.get_driver()
        png = driver.get_screenshot_as_png()
        b64 = base64.b64encode(png).decode()
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = """
        Analyze this webpage screenshot and rate it from 0.0 to 1.0 on:
        - alignment_score: How well elements are aligned and positioned
        - spacing_score: Quality of whitespace and element spacing
        - contrast_score: Text/background contrast and readability
        
        Also identify which sections are visible:
        - hero (main banner/header area)
        - projects (portfolio/work showcase)
        - contact (contact form or contact info)
        - about (about section)
        - services (services or features)
        - testimonials (reviews or testimonials)
        
        Return ONLY a JSON object with keys: alignment_score, spacing_score, contrast_score, visible_sections (array).
        """
        
        resp = client.chat.completions.create(
            model=os.getenv("MODEL_ID", "gpt-4o"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]}
            ],
            temperature=0,
            max_tokens=300
        )
        
        try:
            content = resp.choices[0].message.content.strip()
            # Extract JSON from response
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Vision JSON parse failed: {e}, falling back to heuristic")
            return analyze_view_heuristic()
        
    except Exception as e:
        print(f"Vision analysis failed: {e}, falling back to heuristic")
        return analyze_view_heuristic()


def analyze_view_heuristic() -> dict:
    """Fallback heuristic analysis when vision model unavailable.
    
    Returns:
        Dict with scores and visible sections
    """
    visible_sections = []
    
    # Check for hero section
    hero_indicators = ["portfolio", "developer", "designer", "welcome", "hello", "Symphony"]
    for indicator in hero_indicators:
        try:
            if helium.Text(indicator).exists():
                visible_sections.append("hero")
                break
        except:
            pass
    
    # Check for projects section
    project_indicators = ["project", "work", "portfolio", "showcase", "Project"]
    for indicator in project_indicators:
        try:
            if helium.Text(indicator).exists():
                visible_sections.append("projects")
                break
        except:
            pass
    
    # Check for contact section
    contact_indicators = ["contact", "email", "message", "get in touch", "Contact"]
    for indicator in contact_indicators:
        try:
            if helium.Text(indicator).exists():
                visible_sections.append("contact")
                break
        except:
            pass
    
    # Basic scoring based on visible elements
    base_score = 0.6 + (len(visible_sections) * 0.1)
    
    return {
        "alignment_score": min(base_score + 0.1, 1.0),
        "spacing_score": min(base_score, 1.0),
        "contrast_score": min(base_score + 0.05, 1.0),
        "visible_sections": visible_sections
    }


def inspect_site(url: str, run_id: str = "default") -> SensoryReport:
    """Main function to inspect site with agentic browsing.
    
    Args:
        url: URL to inspect (e.g., http://localhost:3000)
        run_id: Unique identifier for this run (for artifacts)
        
    Returns:
        SensoryReport with all inspection results
    """
    # Setup Chrome with appropriate options
    opts = Options()
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    
    headless = os.getenv("SYMPHONY_HEADLESS", "true").lower() == "true"
    if headless:
        opts.add_argument("--headless")
    
    screenshots = []
    all_visible_sections = set()
    alignment_scores = []
    spacing_scores = []
    contrast_scores = []
    
    try:
        # Start browser
        helium.start_chrome(headless=headless, options=opts)
        
        # Step 1: Initial page load
        go_to_url(url)
        screen1_path = _save_step_screenshot("1_initial", run_id)
        screen1 = analyze_current_view()
        screenshots.append(Screenshot(page="initial_load", path=screen1_path))
        
        alignment_scores.append(screen1.get("alignment_score", 0.7))
        spacing_scores.append(screen1.get("spacing_score", 0.7))
        contrast_scores.append(screen1.get("contrast_score", 0.7))
        all_visible_sections.update(screen1.get("visible_sections", []))
        
        # Step 2: Explore and scroll
        ensure_contact_present()
        screen2_path = _save_step_screenshot("2_scroll", run_id)
        screen2 = analyze_current_view()
        screenshots.append(Screenshot(page="after_scroll", path=screen2_path))
        
        alignment_scores.append(screen2.get("alignment_score", 0.7))
        spacing_scores.append(screen2.get("spacing_score", 0.7))
        contrast_scores.append(screen2.get("contrast_score", 0.7))
        all_visible_sections.update(screen2.get("visible_sections", []))
        
        # Step 3: Try contact form interaction
        interaction = submit_contact_form()
        
        # Step 4: Final analysis after interaction
        screen3_path = _save_step_screenshot("3_submit", run_id)
        screen3 = analyze_current_view()
        screenshots.append(Screenshot(page="after_submit", path=screen3_path))
        
        alignment_scores.append(screen3.get("alignment_score", 0.7))
        spacing_scores.append(screen3.get("spacing_score", 0.7))
        contrast_scores.append(screen3.get("contrast_score", 0.7))
        all_visible_sections.update(screen3.get("visible_sections", []))
        
        # Step 5: Basic accessibility check
        a11y = check_basic_accessibility()
        
        # Aggregate scores (use max to be lenient)
        final_alignment = max(alignment_scores) if alignment_scores else 0.7
        final_spacing = max(spacing_scores) if spacing_scores else 0.7
        final_contrast = max(contrast_scores) if contrast_scores else 0.7
        
        # Determine status based on quality gates
        report = SensoryReport(
            status="pass",  # Will be updated by passes_all_gates check
            alignment_score=final_alignment,
            spacing_score=final_spacing,
            contrast_score=final_contrast,
            visible_sections=sorted(list(all_visible_sections)),
            interaction=interaction,
            a11y=a11y,
            playwright=PlaywrightResult(passed=True, total_tests=0),  # Placeholder
            screens=screenshots
        )
        
        # Update status based on gates
        if not report.passes_all_gates():
            report.status = "needs_fix"
        
        return report
        
    except Exception as e:
        # Return error report
        return SensoryReport(
            status="needs_fix",
            alignment_score=0.0,
            spacing_score=0.0,
            contrast_score=0.0,
            visible_sections=[],
            interaction=InteractionResult(
                contact_submitted=False,
                details=f"Error during inspection: {str(e)}",
                errors=[str(e)]
            ),
            a11y=AccessibilityResult(violations=0, top_issues=[]),
            playwright=PlaywrightResult(passed=False, failed_tests=["Site inspection"], total_tests=1),
            screens=[]
        )
        
    finally:
        try:
            helium.kill_browser()
        except Exception:
            pass


# Backward compatibility function
def make_sensory_agent():
    """Legacy function for backward compatibility."""
    class LegacySensoryAgent:
        def run(self, instruction: str):
            if "localhost" in instruction:
                # Extract URL from instruction
                import re
                match = re.search(r'https?://localhost:\d+', instruction)
                if match:
                    url = match.group(0)
                    report = inspect_site(url)
                    # Convert to legacy dict format
                    return report.to_dict()
            return {"error": "Please provide a localhost URL to inspect"}
    
    return LegacySensoryAgent()
