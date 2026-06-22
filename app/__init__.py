import os

from flask import Flask


def should_start_background_updates():
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return True

    return os.environ.get("START_BACKGROUND_UPDATES", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def create_app():
    app = Flask(__name__)

    from app.routes import main, start_background_updates
    app.register_blueprint(main)

    if should_start_background_updates():
        start_background_updates()

    return app
