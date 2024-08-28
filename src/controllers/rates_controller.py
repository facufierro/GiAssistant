from flask import Blueprint, jsonify
from src.services.rates_service import RatesService

rates_bp = Blueprint('rates', __name__)


@rates_bp.route('/update-rates', methods=['GET'])
def update_rates():
    service = RatesService()
    try:
        service.update_rates()
        return jsonify({"message": "Rates updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to update rates: {str(e)}"}), 500
