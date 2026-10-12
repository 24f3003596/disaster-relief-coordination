from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash

from extensions import db
from auth import auth_bp
from incidents import incidents_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="change-this-to-a-random-secret-before-deployment",
        SQLALCHEMY_DATABASE_URI="sqlite:///disaster_relief.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")

    @app.get("/")
    def index():
        return jsonify({
            "project": "Disaster Relief Resource Coordination System",
            "status": "running",
            "endpoints": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "current_user": "GET /auth/me",
                "create_incident": "POST /incidents/",
                "list_incidents": "GET /incidents/",
                "affected_areas": "GET /incidents/affected-areas",
            },
        })

    with app.app_context():
        # Import models so SQLAlchemy registers them before create_all.
        import models  # noqa: F401
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
