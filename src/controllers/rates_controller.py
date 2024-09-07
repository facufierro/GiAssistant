# path:  src/services/rates_service.py
from flask import Blueprint, jsonify
from src.services.rates_service import RatesService

rates_controller = Blueprint('rates', __name__)


@rates_controller.route('/update-rates', methods=['GET'])
def update_rates():
    service = RatesService()
    try:
        service.update_rates()
        return jsonify({"message": "Rates updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to update rates: {str(e)}"}), 500
