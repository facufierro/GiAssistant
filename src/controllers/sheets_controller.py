from flask import Blueprint, jsonify
from src.services.sheet_service import SheetService
from src.services.rates_service import RatesService
from src.clients.sheets_client import get_sheet_client
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get Google Sheet ID from .env
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise ValueError("Missing SHEET_ID in .env file")

# Initialize services
sheet_client = get_sheet_client()
sheet_service = SheetService(sheet_client)
rates_service = RatesService()

# Create Blueprint
sheets_bp = Blueprint('sheets', __name__)

# Predefined sheet name and columns
SHEET_NAME = "Ventas"
COLUMNS = ["FECHA DE INGRESO", "COTIZACIÓN OFICIAL", "COTIZACIÓN BLUE"]


@sheets_bp.route('/update_sheet', methods=['GET'])
def update_sheet():
    """
    API route to fetch Google Sheet data, compare with exchange rates, and update values.

    Returns:
        JSON response with success or failure message.
    """
    # Fetch Google Sheets data
    sheet_data = sheet_service.get_dates(
        SHEET_ID, SHEET_NAME, "FECHA DE INGRESO")

    # Get the rates data
    rates_data = rates_service.get_rates()

    # Compare and update rates
    updated_data = rates_service.compare_and_update_rates(
        sheet_data, rates_data)

    # Write the new values back to Google Sheets
    result = sheet_service.write_updated_rates(
        SHEET_ID, SHEET_NAME, updated_data)

    return jsonify(result)
