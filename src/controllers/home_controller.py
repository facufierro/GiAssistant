# path: src/controllers/home_controller.py
from flask import Blueprint, jsonify

home_controller = Blueprint('home_controller', __name__)


@home_controller.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'giassistant is running'}), 200
