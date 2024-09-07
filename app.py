# path: app.py
import os
import shutil
from flask import Flask
from src.controllers.rates_controller import rates_controller
from src.controllers.home_controller import home_controller


def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(home_controller, url_prefix='/gi')
    app.register_blueprint(rates_controller, url_prefix='/gi/rates')

    return app


def clear_pycache():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            shutil.rmtree(pycache_path)


if __name__ == "__main__":
    app = create_app()
    clear_pycache()
    app.run(host='0.0.0.0', port=5000)
