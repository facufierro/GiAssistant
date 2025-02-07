from flask import Flask
from src.controllers.rates_controller import rates_bp
from src.controllers.sheets_controller import sheets_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(rates_bp)
    app.register_blueprint(sheets_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
