# path: src/controllers/home_controller.py
from flask import Blueprint, jsonify
from src.models import spreadsheet_ventas_2024

home_controller = Blueprint('home_controller', __name__)


@home_controller.route('/', methods=['GET'])
def index():
    worksheet_names = list(spreadsheet_ventas_2024.worksheets.keys())
    return jsonify({'message': 'giassistant is running', 'worksheets': worksheet_names}), 200
