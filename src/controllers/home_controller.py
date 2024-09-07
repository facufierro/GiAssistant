# path: src/controllers/home_controller.py
from flask import Blueprint, jsonify
from src.models import spreadsheet_ventas_2024

home_controller = Blueprint('home_controller', __name__)


@home_controller.route('/', methods=['GET'])
def index():
    value = spreadsheet_ventas_2024.worksheets['Ventas'].cells[3,3].value
    return jsonify({'message': 'giassistant is running', 'value': value}), 200
