# path: models/__init__.py

import os
from dotenv import load_dotenv
from src.models.spreadsheet import Spreadsheet

load_dotenv()
spreadsheet_ventas_2024 = Spreadsheet(sheet_key=os.getenv('DEV_PREVENTAS_VENTA_2024'), credentials_file=os.getenv('CREDENTIALS_FILE_PATH'))
