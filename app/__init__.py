import os

from flask import Flask


def create_app():
    app = Flask(__name__)

    from app.routes import main, start_background_updates
    app.register_blueprint(main)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_background_updates()

    return app
