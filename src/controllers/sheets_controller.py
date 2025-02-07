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


@sheets_bp.route('/get_column', methods=['GET'])
def get_column():
    """
    API route to fetch a specific column from a Google Sheet.

    Query Parameters:
        - sheet_name (str): The name of the worksheet (tab) inside the sheet.
        - column (str): The name of the column to retrieve.

    Example:
        GET /get_column?sheet_name=Ventas&column=COTIZACIÓN OFICIAL

    Returns:
        JSON response with the column data or an error message.
    """
    sheet_name = request.args.get('sheet_name')
    column_name = request.args.get('column')

    # Validate required parameters
    if not sheet_name or not column_name:
        return jsonify({"error": "Missing required parameters: 'sheet_name' and 'column'"}), 400

    # Retrieve and return column data using SHEET_ID from .env
    return sheet_service.get_column_as_json(SHEET_ID, sheet_name, column_name)
