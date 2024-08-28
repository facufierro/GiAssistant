# path: src/models/spreadsheet.py

import gspread
from google.oauth2.service_account import Credentials
from src.models.worksheet import Worksheet
import logging


class Spreadsheet:
    def __init__(self, sheet_key, credentials_file):
        self.sheet_key = sheet_key
        self.credentials_file = credentials_file
        self.client = self._authorize_client()
        self.worksheets = self._initialize_worksheets()

    def _authorize_client(self):
        """
        Authorize and return a Google Sheets client.
        """
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            credentials = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            client = gspread.authorize(credentials)
            logging.info("Google Sheets client authorized successfully.")
            return client
        except Exception as e:
            logging.error(f"Failed to authorize Google Sheets client: {e}")
            return None

    def _initialize_worksheets(self):
        """
        Initialize and store each worksheet in a dictionary
        with the worksheet title as the key.
        """
        try:
            spreadsheet = self.client.open_by_key(self.sheet_key)
            worksheets = {ws.title: Worksheet(ws) for ws in spreadsheet.worksheets()}
            logging.info(f"Spreadsheet with key {self.sheet_key} initialized successfully.")
            return worksheets
        except Exception as e:
            logging.error(f"Failed to initialize spreadsheet: {e}")
            return {}

    def get_worksheet(self, title):
        """
        Retrieve a Worksheet object by its title.
        """
        worksheet = self.worksheets.get(title)
        if worksheet:
            logging.info(f"Worksheet '{title}' retrieved successfully.")
        else:
            logging.error(f"Worksheet '{title}' not found in the spreadsheet.")
        return worksheet

    def add_worksheet(self, title, rows, cols):
        """
        Add a new worksheet to the spreadsheet.
        """
        if title in self.worksheets:
            logging.error(f"Worksheet '{title}' already exists. Cannot add a new one with the same title.")
            return None

        try:
            spreadsheet = self.client.open_by_key(self.sheet_key)
            worksheet = spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
            self.worksheets[title] = Worksheet(worksheet)
            logging.info(f"Worksheet '{title}' added successfully.")
            return self.worksheets[title]
        except Exception as e:
            logging.error(f"Failed to add worksheet '{title}': {e}")
            return None

    def delete_worksheet(self, title):
        """
        Delete a worksheet by its title.
        """
        worksheet = self.get_worksheet(title)
        if worksheet is None:
            logging.error(f"Cannot delete worksheet '{title}' because it was not found.")
            return

        try:
            worksheet.gspread_worksheet.delete()
            del self.worksheets[title]
            logging.info(f"Worksheet '{title}' deleted successfully.")
        except Exception as e:
            logging.error(f"Failed to delete worksheet '{title}': {e}")

    def list_worksheets(self):
        """
        List all worksheet titles in the spreadsheet.
        """
        return list(self.worksheets.keys())
