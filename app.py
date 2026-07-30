"""
app.py - AAVA (AI Agricultural Voice Assistant) entry point.

Run with:
    python app.py
Then visit http://localhost:5000 for the browser demo dashboard,
or point a Twilio phone number's webhook at /voice/incoming for a
real phone-call deployment.
"""

import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from routes.voice_routes import voice_bp  # noqa: E402  (import after load_dotenv)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    app.register_blueprint(voice_bp)

    @app.get("/api/health")
    def health():
        # Used by uptime monitoring to track the 99.9% availability KPI
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
