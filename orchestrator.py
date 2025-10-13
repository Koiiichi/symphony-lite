from agents.brain_agent import brain_agent
from agents.sensory_agent import make_sensory_agent
from runner import run_servers

def main():
    goal = "Create a dark-themed portfolio with projects grid and contact form"
    print(f"[System] Goal: {goal}")

    # 1. Brain generates code
    instructions = f"""
    Generate React frontend + Flask backend for: {goal}
    
    Please create the following files:
    - frontend/index.html: A standalone HTML file with CSS and JavaScript
    - frontend/package.json: Package configuration for React/Node.js
    - backend/app.py: Flask backend with contact form API
    - backend/requirements.txt: Python dependencies
    
    Use the write_code function to save each file. Paths should be relative to projects/portfolio/.
    """
    brain_agent.run(instructions)

    # 2. Start local servers
    backend_proc, frontend_proc = run_servers()

    # 3. Sensory inspects visuals
    sensory = make_sensory_agent()
    feedback = sensory.run("Go to http://localhost:3000 and evaluate layout visuals in JSON")

    print("\n[Sensory Feedback]\n", feedback)

    # 4. Brain fixes issues based on feedback
    brain_agent.run(f"Improve layout and code based on feedback: {feedback}")

if __name__ == "__main__":
    main()
