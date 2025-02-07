import gspread
import logging
from flask import jsonify


class SheetService:
    """
    Service class for retrieving a column from a specified Google Sheet and returning it as JSON.

    Attributes:
        sheet_client: An instance of the Google Sheets client.
    """

    def __init__(self, sheet_client):
        """
        Initializes the SheetService with the Google Sheets client.

        Args:
            sheet_client: An authenticated gspread client.
        """
        self.sheet_client = sheet_client

    def get_column_as_json(self, sheet_id, sheet_name, column_name):
        """
        Retrieves a specific column from a specified Google Sheet and worksheet.

        Args:
            sheet_id (str): The Google Sheet ID.
            sheet_name (str): The worksheet (tab) name within the sheet.
            column_name (str): The name of the column to retrieve.

        Returns:
            JSON response containing the column data.
        """
        try:
            # Open the Google Sheet by ID and worksheet name
            sheet = self.sheet_client.open_by_key(
                sheet_id).worksheet(sheet_name)

            # Get column values (Find the column index dynamically)
            headers = sheet.row_values(1)  # Get the first row (headers)
            if column_name not in headers:
                return jsonify({"error": f"Column '{column_name}' not found"}), 404

            # Convert to 1-based index
            col_index = headers.index(column_name) + 1
            column_values = sheet.col_values(
                col_index)[1:]  # Skip the header row

            return jsonify({column_name: column_values}), 200

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Sheet with ID '{sheet_id}' not found.")
            return jsonify({"error": f"Sheet with ID '{sheet_id}' not found"}), 404

        except gspread.exceptions.WorksheetNotFound:
            logging.error(
                f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'.")
            return jsonify({"error": f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'"}), 404

        except Exception as e:
            logging.error(f"Error retrieving column '{column_name}': {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
