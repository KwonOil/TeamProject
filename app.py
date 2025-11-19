"""TeamProject Flask web server."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        """Render a simple landing page with server information."""
        return render_template("index.html", server_time=datetime.utcnow())

    @app.route("/api/health")
    def health() -> Dict[str, Any]:
        """Expose a tiny health endpoint useful for uptime checks."""
        return jsonify(
            {
                "status": "ok",
                "message": "TeamProject Flask server is running",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "client": request.remote_addr,
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
