from flask import Blueprint, jsonify, request
from src.services.rates_service import RatesService

rates_bp = Blueprint('rates', __name__)
service = RatesService()


@rates_bp.route('/get_rates', methods=['GET'])
def get_rates():
    """
    API route to fetch exchange rate data.

    Query Parameters (Optional):
        - dates: Comma-separated list of dates (YYYY-MM-DD,YYYY-MM-DD)
        - source: The exchange rate source (e.g., "Oficial", "Blue")

    Behavior:
        - If no parameters are provided, return the full dataset.
        - If 'dates' and 'source' are provided, filter the results accordingly.

    Example Calls:
        - GET /get_rates  -> Returns full dataset
        - GET /get_rates?dates=2025-02-07,2025-02-05&source=Blue -> Returns filtered results

    Returns:
        JSON response with exchange rates or an error message.
    """
    # Get query parameters
    dates_param = request.args.get('dates')
    source = request.args.get('source')

    # If no parameters provided, return full dataset
    if not dates_param and not source:
        all_rates = service.get_rates()
        return jsonify(all_rates) if all_rates else jsonify({"message": "No data available"}), 500

    # Validate required parameters for filtering
    if not dates_param or not source:
        return jsonify({"error": "Missing required parameters: 'dates' and 'source'"}), 400

    # Convert comma-separated string to list of dates
    dates_list = dates_param.split(",")

    # Fetch filtered rates
    filtered_rates = service.filter_rates(dates_list, source)

    # Return the filtered rates or a message if no data found
    return jsonify(filtered_rates) if filtered_rates else jsonify({"message": "No rates found"}), 404
