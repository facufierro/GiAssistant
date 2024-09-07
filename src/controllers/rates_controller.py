from flask import Blueprint, jsonify
from src.services.rates_service import RatesService
from src.models import spreadsheet_ventas_2024  # Import your already initialized spreadsheet object
from src.utils.data_processor import DataProcessor  # Assuming DataProcessor is implemented

rates_controller = Blueprint('rates', __name__)


@rates_controller.route('/update', methods=['GET'])
def update():
    try:
        # Initialize the data processor and the service
        data_processor = DataProcessor()  # Assuming this is implemented
        rates_service = RatesService(spreadsheet_ventas_2024, data_processor)  # Use the spreadsheet_x directly

        # Call the update method (replace with actual worksheet and column names)
        rates_service.update('Ventas', 'Date', 'Rate', 'oficial')  # Example: "Ventas" worksheet

        return jsonify({"message": "Rates updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to update rates: {str(e)}"}), 500
