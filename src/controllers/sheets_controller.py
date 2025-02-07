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
    SHEET_NAME = "Ventas"  # Ensure this matches your actual sheet tab name
    # Ensure this column exists in your sheet
    COLUMN_FECHA_INGRESO = "FECHA DE INGRESO"
    COLUMN_FECHA_VENTA = "FECHA DE VENTA"  # Ensure this column exists in your sheet

    # Fetch Google Sheets data
    sheet_data = sheet_service.get_dates(
        SHEET_ID, SHEET_NAME, COLUMN_FECHA_INGRESO, COLUMN_FECHA_VENTA  # ✅ Pass both columns
    )

    # Get the rates data
    rates_data = rates_service.get_rates()

    if not isinstance(sheet_data, dict):  # Ensure it's always a dictionary
        raise TypeError(f"Expected dict, got {type(sheet_data)}")

    if "data" not in sheet_data:  # Ensure "data" key exists
        raise KeyError(f"Missing 'data' key in sheet_data: {sheet_data}")

    updated_data = rates_service.compare_and_update_rates(
        sheet_data["data"], rates_data  # ✅ Ensure correct dictionary key
    )

    # Write the new values back to Google Sheets
    result = sheet_service.write_updated_rates(
        SHEET_ID, SHEET_NAME, updated_data
    )

    return jsonify(result)
