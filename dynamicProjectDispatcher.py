from flask import Flask
import importlib
import os
import json
from werkzeug.wrappers import Request, Response

class DynamicProjectDispatcher:
    """
    WSGI middleware that dynamically loads
    Flask apps per project on request
    """

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
                return child_app
            else:
                print(f"❌ No Flask app found in {module_path}")
                return None
        except Exception as e:
            print(f"❌ Failed loading {project_name}: {e}")
            return None

    def __call__(self, environ, start_response):
        request = Request(environ)
        path = request.path.strip("/")
        if not path:
            return self.app(environ, start_response)

        parts = path.split("/")
        project_name = parts[0]
        project_path = os.path.join(self.projects_dir, project_name)

        if os.path.isdir(project_path):
            child_app = self.load_project(project_name)
            if child_app:
                new_path = "/" + "/".join(parts[1:])
                environ["PATH_INFO"] = new_path if new_path != "/" else "/"
                environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/" + project_name
                return child_app(environ, start_response)
            return Response(
                f"Failed to load project: {project_name}",
                status=500
            )(environ, start_response)

        return self.app(environ, start_response)

    def find_flask_app(self, module):
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Flask):
                print(f"✅ Found Flask app: {attr_name}")
                return attr
        return None