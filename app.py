import os
import subprocess
import re
import json
from flask import Flask, jsonify, request, render_template
from werkzeug.serving import run_simple
from dynamicProjectDispatcher import DynamicProjectDispatcher

PROJECTS_DIR = "projects"
DB_FILE = "projects_db.json"

def get_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

app = Flask(__name__)

@app.route("/")
def home():
    db = get_db()
    projects = []
    if os.path.exists(PROJECTS_DIR):
        for name in os.listdir(PROJECTS_DIR):
            if os.path.isdir(os.path.join(PROJECTS_DIR, name)) and not name.startswith('.') and name != "__pycache__":
                projects.append({
                    "name": name,
                    "entry_point": db.get(name, {}).get("entry_point", "app.py")
                })
    return render_template("index.html", projects=projects)

@app.route("/projects")
def list_projects():
    """
    Lists all available project folders
    """
    projects = [
        name for name in os.listdir(PROJECTS_DIR)
        if os.path.isdir(os.path.join(PROJECTS_DIR, name))
    ]

    return jsonify({
        "available_projects": projects
    })

@app.route("/clone-project", methods=["POST"])
def clone_project():
    data = request.json
    repo_url = data.get("repo_url")
    entry_point = data.get("entry_point", "app.py").strip()
    
    # Remove .py from entry_point if provided
    if entry_point.endswith(".py"):
        entry_point = entry_point[:-3]
    
    if not repo_url:
        return jsonify({"error": "No repository URL provided"}), 400

    # Extract project name from URL
    match = re.search(r"/([^/]+?)(?:\.git)?$", repo_url)
    if not match:
        return jsonify({"error": "Invalid git URL"}), 400
    
    project_name = match.group(1)
    target_path = os.path.join(PROJECTS_DIR, project_name)

    if os.path.exists(target_path):
        return jsonify({"error": f"Project '{project_name}' already exists"}), 409

    try:
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        
        process = subprocess.run(
            ["git", "clone", repo_url, target_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        init_file = os.path.join(target_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass
        
        root_init = os.path.join(PROJECTS_DIR, "__init__.py")
        if not os.path.exists(root_init):
            with open(root_init, "w") as f:
                pass

        db = get_db()
        db[project_name] = {
            "repo_url": repo_url,
            "entry_point": entry_point
        }
        save_db(db)

        return jsonify({
            "success": True,
            "project_name": project_name,
            "message": f"Successfully cloned {project_name} (Entry: {entry_point}.py)"
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Git clone failed",
            "details": e.stderr
        }), 500
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

application = DynamicProjectDispatcher(app)

if __name__ == "__main__":
    run_simple(
        hostname="0.0.0.0",
        port=5000,
        application=application,
        use_debugger=True,
        use_reloader=True
    )
