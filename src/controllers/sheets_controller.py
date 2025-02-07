from flask import Blueprint, request, jsonify
from src.services.sheet_service import SheetService
from src.clients.sheets_client import get_sheet_client
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get Google Sheet ID from .env
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise ValueError("Missing SHEET_ID in .env file")

# Initialize Google Sheets client
sheet_client = get_sheet_client()
sheet_service = SheetService(sheet_client)

# Create Blueprint for Sheets API
sheets_bp = Blueprint('sheets', __name__)


@sheets_bp.route('/get_values', methods=['GET'])
def get_values():
    """
    API route to fetch values along with row numbers from specified Google Sheet columns.

    Query Parameters:
        - sheet_name (str): The name of the worksheet (tab) inside the sheet.
        - columns (str): Comma-separated list of column names.

    Example:
        GET /get_values?sheet_name=Ventas&columns=COTIZACIÓN OFICIAL,Fecha

    Returns:
        JSON response with values and row numbers.
    """
    sheet_name = request.args.get('sheet_name')
    columns_param = request.args.get('columns')

    # Validate required parameters
    if not sheet_name or not columns_param:
        return jsonify({"error": "Missing required parameters: 'sheet_name' and 'columns'"}), 400

    # Convert comma-separated string to list of column names
    column_names = [col.strip() for col in columns_param.split(",")]

    # Retrieve and return column data
    return sheet_service.get_values_with_rows(SHEET_ID, sheet_name, column_names)
