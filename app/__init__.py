import os

from flask import Flask


def init_sentry():
    dsn = os.environ.get("SENTRY_DSN", "").strip()

    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
    except ImportError:
        return False

    try:
        traces_sample_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.05"))
    except ValueError:
        traces_sample_rate = 0.05

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=max(0.0, min(traces_sample_rate, 1.0)),
        environment=os.environ.get("APP_ENV", "production"),
        release=os.environ.get("RENDER_GIT_COMMIT", ""),
        send_default_pii=False,
    )
    return True


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
    sentry_enabled = init_sentry()
    app = Flask(__name__)

    @app.context_processor
    def inject_monitoring_config():
        return {
            "ga_measurement_id": os.environ.get("GA_MEASUREMENT_ID", "").strip(),
            "monitoring_enabled": sentry_enabled or bool(os.environ.get("CLIENT_ERROR_LOGGING", "").strip()),
        }

    from app.routes import main, start_background_updates
    app.register_blueprint(main)

    if should_start_background_updates():
        start_background_updates()

    return app
