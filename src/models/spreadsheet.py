# path: src/models/spreadsheet.py
import logging
import gspread
from google.oauth2.service_account import Credentials
from .worksheet import Worksheet


class Spreadsheet:
    def __init__(self, sheet_key, credentials_file):
        self.sheet_key = sheet_key
        self.credentials_file = credentials_file
        self.client = self._authorize_client()
        self.worksheets = self._load_worksheets()

    def _authorize_client(self):
        creds = Credentials.from_service_account_file(self.credentials_file, scopes=['https://spreadsheets.google.com/feeds'])
        return gspread.authorize(creds)

    def _load_worksheets(self):
        spreadsheet = self.client.open_by_key(self.sheet_key)
        worksheets = {}
        for ws in spreadsheet.worksheets():
            worksheets[ws.title] = Worksheet(ws)
        return worksheets

    def __getattr__(self, name):
        if name in self.worksheets:
            return self.worksheets[name]
        raise AttributeError(f"Worksheet '{name}' not found in the spreadsheet.")
