import gspread
import logging
from flask import jsonify
from datetime import datetime


class SheetService:
    """
    Service class for retrieving multiple columns and their row numbers from a Google Sheet.

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

    def get_values_with_rows(self, sheet_id, sheet_name, column_names):
        """
        Retrieves specific columns from a Google Sheet, returning values along with their row numbers.

        Args:
            sheet_id (str): The Google Sheet ID.
            sheet_name (str): The worksheet (tab) name within the sheet.
            column_names (list): A list of column names to retrieve.

        Returns:
            JSON response containing values and their row numbers.
        """
        try:
            # Open the Google Sheet by ID and worksheet name
            sheet = self.sheet_client.open_by_key(
                sheet_id).worksheet(sheet_name)

            # Get the headers (first row) to determine column indices
            headers = sheet.row_values(1)
            column_indices = {}

            for col_name in column_names:
                if col_name in headers:
                    column_indices[col_name] = headers.index(
                        col_name) + 1  # Convert to 1-based index
                else:
                    logging.warning(f"Column '{col_name}' not found")

            if not column_indices:
                return jsonify({"error": "None of the specified columns were found"}), 404

            # Get data for each column
            row_data = {}
            for col_name, col_index in column_indices.items():
                column_values = sheet.col_values(
                    col_index)[1:]  # Exclude the header

                # Start from row 2 (after headers)
                for row_num, value in enumerate(column_values, start=2):
                    if row_num not in row_data:
                        row_data[row_num] = {"row": row_num}

                    # Convert date format if necessary
                    row_data[row_num][col_name] = self._format_dates(
                        value)

            return jsonify({"data": list(row_data.values())}), 200

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Sheet with ID '{sheet_id}' not found.")
            return jsonify({"error": f"Sheet with ID '{sheet_id}' not found"}), 404

        except gspread.exceptions.WorksheetNotFound:
            logging.error(
                f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'.")
            return jsonify({"error": f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'"}), 404

        except Exception as e:
            logging.error(
                f"Error retrieving columns '{column_names}': {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    def _format_dates(self, value):
        """
        Converts a date from 'D/M/YYYY' or 'DD/MM/YYYY' format to 'YYYY-MM-DD' format if necessary.

        Args:
            value (str): The cell value from the Google Sheet.

        Returns:
            str: The converted date in 'YYYY-MM-DD' format or the original value if not a date.
        """
        try:
            # Check if the value follows a date pattern with "/" separator
            if isinstance(value, str) and "/" in value:
                # Handle missing leading zeros (e.g., "1/2/2020" → "01/02/2020")
                parts = value.split("/")
                if len(parts) == 3:
                    day, month, year = parts
                    day = day.zfill(2)  # Ensure two-digit day
                    month = month.zfill(2)  # Ensure two-digit month
                    formatted_date = f"{day}/{month}/{year}"

                    # Convert to YYYY-MM-DD
                    return datetime.strptime(formatted_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass  # Ignore conversion errors, return the original value

        return value  # Return unchanged if it's not a date
