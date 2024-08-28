# path: app.py
from flask import Flask
from src.controllers.rates_controller import rates_bp


def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(rates_bp, url_prefix='/gi')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
