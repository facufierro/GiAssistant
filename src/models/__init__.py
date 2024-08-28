# path: modules/__init__.py

import os
from dotenv import load_dotenv
from src.models.spreadsheet import Spreadsheet

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
GOOGLE_SHEET_KEY = os.getenv('DEV_PREVENTAS_VENTA_2024')
CREDENTIALS_FILE_PATH = os.getenv('CREDENTIALS_FILE_PATH')

# Initialize the Spreadsheet object using the environment variables
spreadsheet_x = Spreadsheet(sheet_key=GOOGLE_SHEET_KEY, credentials_file=CREDENTIALS_FILE_PATH)

# Optionally, access a specific worksheet by name (example)
worksheet_x = spreadsheet_x.get_worksheet("Ventas")
