
paths = [
    "frontend/index.html", "frontend/package.json", "backend/app.py", "backend/requirements.txt"
]
for p in paths:
    try:
        with open(p, "rb"):
            print(f"{p}:FOUND")
    except Exception:
        print(f"{p}:MISSING")
