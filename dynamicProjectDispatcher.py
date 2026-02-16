from flask import Flask
import importlib
import os
import json
from werkzeug.wrappers import Request, Response

class DynamicProjectDispatcher:
    def __init__(self, app, projects_dir="projects", db_file="projects_db.json"):
        self.app = app
        self.projects_dir = projects_dir
        self.db_file = db_file

    def get_project_config(self, project_name):
        if not os.path.exists(self.db_file):
            return {}
        try:
            with open(self.db_file, "r") as f:
                db = json.load(f)
                return db.get(project_name, {})
        except:
            return {}

    def load_project(self, project_name):
        try:
            config = self.get_project_config(project_name)
            entry_point = config.get("entry_point", "app")
            module_path = f"{self.projects_dir}.{project_name}.{entry_point}"
            module = importlib.import_module(module_path)
            child_app = self.find_flask_app(module)
            
            if child_app:
                print(f"✅ Loaded project: {project_name} (via {entry_point}.py)")
                return child_app, None
            else:
                return None, f"No Flask app found in {module_path}. Make sure you have a 'Flask(__name__)' instance in that file."
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Failed loading {project_name}:\n{error_details}")
            return None, error_details

    def __call__(self, environ, start_response):
        request = Request(environ)
        path = request.path.strip("/")
        if not path:
            return self.app(environ, start_response)

        parts = path.split("/")
        project_name = parts[0]
        project_path = os.path.join(self.projects_dir, project_name)

        if os.path.isdir(project_path):
            config = self.get_project_config(project_name)
            
            project_envs = config.get("env_vars", {})
            if project_envs:
                os.environ.update(project_envs)

            child_app, error = self.load_project(project_name)
            if child_app:
                new_path = "/" + "/".join(parts[1:])
                environ["PATH_INFO"] = new_path if new_path != "/" else "/"
                environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/" + project_name
                return child_app(environ, start_response)
            
            # Return detailed error to the client
            error_html = f"""
            <div style="font-family: sans-serif; padding: 2rem; background: #fff1f2; color: #991b1b; border: 1px solid #fecaca; border-radius: 0.5rem;">
                <h1 style="margin-top: 0;">🚀 Project Load Error</h1>
                <p>Failed to load project <strong>{project_name}</strong>.</p>
                <div style="background: #ffffff; padding: 1rem; border-radius: 0.25rem; border: 1px solid #fecaca; font-family: monospace; overflow: auto; max-height: 400px;">
                    <pre style="margin: 0;">{error}</pre>
                </div>
                <p style="margin-bottom: 0; margin-top: 1rem;"><a href="/" style="color: #991b1b; text-decoration: none; font-weight: bold;">&larr; Back to Dashboard</a></p>
            </div>
            """
            return Response(error_html, status=500, mimetype='text/html')(environ, start_response)


        return self.app(environ, start_response)

    def find_flask_app(self, module):
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Flask):
                print(f"✅ Found Flask app: {attr_name}")
                return attr
        return None