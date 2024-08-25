# path: clients/google_sheets_client.py
import logging
import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetClient:
    def __init__(self, sheet_key, sheet_name, credentials_file):
        self.sheet = self._initialize_sheet(sheet_key, sheet_name, credentials_file)

    @staticmethod
    def _initialize_sheet(sheet_key, sheet_name, credentials_file):
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(sheet_key).worksheet(sheet_name)

    def get_column_values(self, column_name):
        headers = self.sheet.row_values(1)
        try:
            col_index = headers.index(column_name) + 1
            column_values = self.sheet.col_values(col_index)
            logging.info(f"Successfully retrieved column '{column_name}' values.")
            return {row_num: value for row_num, value in enumerate(column_values[1:], start=2)}, col_index
        except ValueError:
            logging.error(f"Column '{column_name}' not found.")
            return None, None

    def update_column(self, col_index, values):
        if values:
            range_start = 2
            range_end = range_start + len(values) - 1
            range_name = f"{gspread.utils.rowcol_to_a1(range_start, col_index)}:{gspread.utils.rowcol_to_a1(range_end, col_index)}"
            self.sheet.update(range_name, values)
            logging.info(f"Column at index {col_index} updated successfully with new data.")
