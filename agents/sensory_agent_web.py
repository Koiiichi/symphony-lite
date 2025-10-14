# agents/sensory_agent_web.py
"""Enhanced sensory agent with agentic browsing, form testing, and vision scoring."""

import helium
import time
import json
import base64
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Optional OpenAI import for vision scoring
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

def _screenshot_to_b64(path: str) -> str:
    """Convert screenshot file to base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def _save_step_screenshot(step_name: str, prefix="artifacts/step") -> str:
    """Save screenshot and return the path."""
    os.makedirs("artifacts", exist_ok=True)
    driver = helium.get_driver()
    path = f"{prefix}_{step_name}_{int(time.time())}.png"
    driver.get_screenshot_as_file(path)
    return path

def go_to_url(url: str) -> str:
    """Navigate to URL and wait for load."""
    helium.go_to(url)
    time.sleep(2.0)
    return f"Opened {url}"

def ensure_contact_present() -> str:
    """Scroll to find contact form section."""
    # Look for contact-related elements
    contact_indicators = ["Contact", "contact", "Get in touch", "Send message"]
    
    for indicator in contact_indicators:
        if helium.Text(indicator).exists():
            # Found contact section, scroll to it
            helium.scroll_down(1200)
            time.sleep(1.5)
            return f"Found and scrolled to contact section ({indicator})"
    
    # If not found, scroll down anyway to explore
    helium.scroll_down(1200)
    time.sleep(1.5)
    return "Scrolled down to explore page; contact section may be below fold"

def click_first_button() -> str:
    """Click the first visible button on the page."""
    try:
        helium.click(helium.Button())
        time.sleep(1.0)
        return "Clicked first button successfully"
    except Exception as e:
        return f"No button clicked: {e}"

def submit_contact_form(name="Test User", email="test@example.com", message="Hello from Symphony-Lite!") -> dict:
    """Attempt to fill and submit contact form."""
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
        
        # Fill email field
        email_filled = False
        for selector in email_selectors:
            try:
                helium.write(email, into=selector)
                email_filled = True
                break
            except:
                continue
        
        # Fill message field
        message_filled = False
        for selector in message_selectors:
            try:
                helium.write(message, into=selector)
                message_filled = True
                break
            except:
                continue
        
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
        
        time.sleep(2.0)  # Wait for response
        
        return {
            "submitted": submit_clicked,
            "fields_filled": {
                "name": name_filled,
                "email": email_filled, 
                "message": message_filled
            },
            "success": name_filled and email_filled and message_filled and submit_clicked
        }
        
    except Exception as e:
        return {
            "submitted": False,
            "error": str(e),
            "success": False
        }

def analyze_current_view() -> dict:
    """Analyze current page view using vision model or fallback heuristics."""
    if not HAS_OPENAI or not os.getenv("OPENAI_API_KEY"):
        # Fallback to basic analysis
        return analyze_view_heuristic()
    
    try:
        # Take screenshot for vision analysis
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
            max_tokens=200
        )
        
        return json.loads(resp.choices[0].message.content)
        
    except Exception as e:
        print(f"Vision analysis failed: {e}")
        return analyze_view_heuristic()

def analyze_view_heuristic() -> dict:
    """Fallback heuristic analysis when vision model unavailable."""
    visible_sections = []
    
    # Check for hero section
    hero_indicators = ["portfolio", "developer", "designer", "welcome", "hello"]
    for indicator in hero_indicators:
        if helium.Text(indicator).exists():
            visible_sections.append("hero")
            break
    
    # Check for projects section
    project_indicators = ["project", "work", "portfolio", "showcase"]
    for indicator in project_indicators:
        if helium.Text(indicator).exists():
            visible_sections.append("projects")
            break
    
    # Check for contact section
    contact_indicators = ["contact", "email", "message", "get in touch"]
    for indicator in contact_indicators:
        if helium.Text(indicator).exists():
            visible_sections.append("contact")
            break
    
    # Basic scoring based on visible elements
    base_score = 0.6 + (len(visible_sections) * 0.1)
    
    return {
        "alignment_score": min(base_score + 0.1, 1.0),
        "spacing_score": min(base_score, 1.0),
        "contrast_score": min(base_score + 0.05, 1.0),
        "visible_sections": visible_sections
    }

def inspect_site(url: str) -> dict:
    """Main function to inspect site with agentic browsing."""
    # Setup Chrome with appropriate options
    opts = Options()
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    
    # Use headless mode in production, visible for debugging
    headless = os.getenv("SYMPHONY_HEADLESS", "true").lower() == "true"
    if headless:
        opts.add_argument("--headless")
    
    report = {
        "url": url,
        "status": "unknown",
        "screens": [],
        "interaction": {},
        "timestamp": time.time()
    }
    
    try:
        # Start browser
        helium.start_chrome(headless=headless, options=opts)
        
        # Step 1: Initial page load
        go_to_url(url)
        screen1 = analyze_current_view()
        screen1["page"] = "initial_load"
        report["screens"].append(screen1)
        
        # Step 2: Explore and scroll
        ensure_contact_present()
        screen2 = analyze_current_view()
        screen2["page"] = "after_scroll"
        report["screens"].append(screen2)
        
        # Step 3: Try contact form interaction
        form_result = submit_contact_form()
        report["interaction"] = form_result
        
        # Step 4: Final analysis after interaction
        screen3 = analyze_current_view()
        screen3["page"] = "after_submit"
        report["screens"].append(screen3)
        
        # Aggregate scores
        alignment_scores = [s.get("alignment_score", 0) for s in report["screens"] if "alignment_score" in s]
        spacing_scores = [s.get("spacing_score", 0) for s in report["screens"] if "spacing_score" in s]
        contrast_scores = [s.get("contrast_score", 0) for s in report["screens"] if "contrast_score" in s]
        
        report["alignment_score"] = max(alignment_scores) if alignment_scores else 0.5
        report["spacing_score"] = max(spacing_scores) if spacing_scores else 0.5
        report["contrast_score"] = max(contrast_scores) if contrast_scores else 0.5
        
        # Determine overall status
        form_working = form_result.get("success", False)
        good_alignment = report["alignment_score"] >= 0.9
        
        if good_alignment and form_working:
            report["status"] = "pass"
        elif good_alignment or form_working:
            report["status"] = "partial"
        else:
            report["status"] = "needs_fix"
        
        # Add summary
        report["summary"] = f"Alignment: {report['alignment_score']:.2f}, Form: {'PASS' if form_working else 'FAIL'}"
        
        return report
        
    except Exception as e:
        report["status"] = "error"
        report["error"] = str(e)
        return report
        
    finally:
        try:
            helium.kill_browser()
        except Exception:
            pass  # Browser already closed

# Backward compatibility
def make_sensory_agent():
    """Legacy function for backward compatibility."""
    class LegacySensoryAgent:
        def run(self, instruction: str):
            if "localhost:3000" in instruction:
                return inspect_site("http://localhost:3000")
            else:
                return {"error": "Please provide a localhost URL to inspect"}
    
    return LegacySensoryAgent()