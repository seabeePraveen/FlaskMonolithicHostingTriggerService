import os
import subprocess
import re
import json
import shutil
import sys
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
    projects = [
        name for name in os.listdir(PROJECTS_DIR)
        if os.path.isdir(os.path.join(PROJECTS_DIR, name))
    ]
    return jsonify({"available_projects": projects})

@app.route("/clone-project", methods=["POST"])
def clone_project():
    data = request.json
    repo_url = data.get("repo_url")
    entry_point = data.get("entry_point", "app.py").strip()
    
    if entry_point.endswith(".py"):
        entry_point = entry_point[:-3]
    
    if not repo_url:
        return jsonify({"error": "No repository URL provided"}), 400

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
            capture_output=True, text=True, check=True
        )
        
        for path in [target_path, PROJECTS_DIR]:
            init_file = os.path.join(path, "__init__.py")
            if not os.path.exists(init_file):
                open(init_file, "w").close()
        env_vars_raw = data.get("env_vars", "")
        env_vars_dict = {}
        if env_vars_raw:
            for line in env_vars_raw.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    env_vars_dict[k.strip()] = v.strip()
            
            with open(os.path.join(target_path, ".env"), "w") as f:
                f.write(env_vars_raw)
        requirements_raw = data.get("requirements", "")
        if requirements_raw:
            req_file = os.path.join(target_path, "requirements.txt")
            with open(req_file, "w") as f:
                f.write(requirements_raw)
            
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file],
                capture_output=True, text=True, check=True
            )
        db = get_db()
        db[project_name] = {
            "repo_url": repo_url,
            "entry_point": entry_point,
            "env_vars": env_vars_dict
        }
        save_db(db)

        return jsonify({
            "success": True,
            "project_name": project_name,
            "message": f"Successfully setup {project_name}"
        })
    except subprocess.CalledProcessError as e:
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        return jsonify({
            "error": "Command execution failed",
            "details": e.stderr or str(e)
        }), 500
    except Exception as e:
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/get-project/<project_name>")
def get_project_details(project_name):
    db = get_db()
    if project_name not in db:
        return jsonify({"error": "Project not found"}), 404
    
    config = db[project_name]
    target_path = os.path.join(PROJECTS_DIR, project_name)
    
    env_content = ""
    if os.path.exists(os.path.join(target_path, ".env")):
        with open(os.path.join(target_path, ".env"), "r") as f:
            env_content = f.read()

    req_content = ""
    if os.path.exists(os.path.join(target_path, "requirements.txt")):
        with open(os.path.join(target_path, "requirements.txt"), "r") as f:
            req_content = f.read()

    return jsonify({
        "name": project_name,
        "repo_url": config.get("repo_url"),
        "entry_point": config.get("entry_point") + ".py" if not config.get("entry_point").endswith(".py") else config.get("entry_point"),
        "env_vars": env_content,
        "requirements": req_content
    })

@app.route("/update-project", methods=["POST"])
def update_project():
    data = request.json
    project_name = data.get("project_name")
    entry_point = data.get("entry_point", "app.py").strip()
    
    if entry_point.endswith(".py"):
        entry_point = entry_point[:-3]
    
    db = get_db()
    if project_name not in db:
        return jsonify({"error": "Project not found"}), 404

    target_path = os.path.join(PROJECTS_DIR, project_name)

    try:
        env_vars_raw = data.get("env_vars", "")
        env_vars_dict = {}
        if env_vars_raw:
            for line in env_vars_raw.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    env_vars_dict[k.strip()] = v.strip()
            
            with open(os.path.join(target_path, ".env"), "w") as f:
                f.write(env_vars_raw)

        requirements_raw = data.get("requirements", "")
        if requirements_raw:
            req_file = os.path.join(target_path, "requirements.txt")
            with open(req_file, "w") as f:
                f.write(requirements_raw)
            
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file],
                capture_output=True, text=True, check=True
            )

        db[project_name]["entry_point"] = entry_point
        db[project_name]["env_vars"] = env_vars_dict
        save_db(db)

        return jsonify({
            "success": True,
            "message": f"Successfully updated {project_name}"
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/delete-project/<project_name>", methods=["DELETE"])
def delete_project(project_name):
    target_path = os.path.join(PROJECTS_DIR, project_name)
    
    try:
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
            
        db = get_db()
        if project_name in db:
            del db[project_name]
            save_db(db)
            
        return jsonify({
            "success": True,
            "message": f"Successfully deleted {project_name}"
        })
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
