# path: src/models/spreadsheet.py
import logging
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Optional
from .worksheet import Worksheet


class Spreadsheet:
    def __init__(self, sheet_key: str, credentials_file: str):
        self.sheet_key: str = sheet_key
        self.credentials_file: str = credentials_file
        self.client: Optional[gspread.Client] = self._authorize_client()
        self.worksheets: Dict[str, Worksheet] = self._load_worksheets()

    def _authorize_client(self) -> Optional[gspread.Client]:
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            credentials = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            client = gspread.authorize(credentials)
            logging.info("Google Sheets client authorized successfully.")
            return client
        except Exception as e:
            logging.error(f"Failed to authorize Google Sheets client: {e}")
            return None

    def _load_worksheets(self) -> Dict[str, Worksheet]:
        spreadsheet = self.client.open_by_key(self.sheet_key)
        worksheets: Dict[str, Worksheet] = {}
        for ws in spreadsheet.worksheets():
            worksheets[ws.title] = Worksheet(ws)
        return worksheets
