from flask import Flask
from src.controllers.sheets_controller import sheets_bp
from src.controllers.rates_controller import rates_bp
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def create_app():
    app = Flask(__name__)
    app.register_blueprint(sheets_bp)
    app.register_blueprint(rates_bp)
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
