import json, os, secrets

from flask import Flask, Blueprint, render_template
from flask_cors import CORS
from flask_restx import Api

from celery import Celery

from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.constants import AppConstants as app_constants
from app.constants import SageMakerConstants as sm_constants
from app.core.SagemakerManager import SagemakerManager

import logging


def init_app():
    """Spawns the application"""

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    CORS(app)

    # Set Flask configuration
    app.config["ERROR_404_HELP"] = False

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")

    os.environ["SECRET_KEY"] = secrets.token_urlsafe(16)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s"
    )
    app.logger.setLevel(logging.DEBUG)

    # Register application endpoints using Blueprint
    blueprint = Blueprint("api", __name__, url_prefix=f"/{app_constants.API_VERSION}")

    authorizations = {
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": 'Enter "Bearer <token>"',
        }
    }

    api = Api(
        blueprint,
        title=app_constants.SERVICE_NAME,
        version=app_constants.API_VERSION,
        description=app_constants.SERVICE_DESCRIPTION,
        doc="/docs/",
        authorizations=authorizations,
    )

    register_namespaces(api)
    app.register_blueprint(blueprint)

    # Register error handlers
    @app.errorhandler(HTTPException)
    def app_error_handler(err):
        response = err.get_response()
        response.data = json.dumps(
            {
                "code": err.code,
                "name": err.name,
                "message": err.description,
            }
        )
        response.content_type = "application/json"
        return response

    @api.errorhandler(HTTPException)
    def api_error_handler(err):
        data = {
            "code": err.code,
            "name": err.name,
        }
        return data, err.code

    # Add route for the HTML page
    @app.route("/signin")
    def index():
        return render_template("signin.html")

    @app.route("/signup")
    def signup():
        return render_template("signup.html")

    @app.route("/")
    def main():
        return render_template("main.html")

    @app.route("/inference")
    def process():
        return render_template("process.html")

    @app.route("/model")
    def upload_m():
        return render_template("model.html")

    @app.route("/view-models")
    def view_model():
        return render_template("view-models.html")

    @app.route("/view-contributors")
    def view_contributor():
        return render_template("view-contributors.html")

    @app.route("/example")
    def example():
        return render_template("example.html")

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    @app.route("/profile")
    def profile():
        return render_template("profile.html")

    # add more routes here
    return app


def register_namespaces(app_api):
    """Adds the namespaces to the application"""
    from app.api.model_manager.controller import ns as model_manager_namespace
    from app.api.inference.controller import ns as inference_namespace
    from app.api.user.controller import ns as user_namespace
    from app.api.model_registry.controller import ns as model_registry_namespace

    app_api.add_namespace(model_manager_namespace, path="/api/model_manager")
    app_api.add_namespace(inference_namespace, path="/api/inference")
    app_api.add_namespace(user_namespace, path="/api/user")
    app_api.add_namespace(model_registry_namespace, path="/api/model_registry")

    # Add more namespaces here
