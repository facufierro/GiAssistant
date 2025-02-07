import gspread
import logging
from flask import jsonify
from datetime import datetime


class SheetService:
    """
    Service class for retrieving and writing multiple columns with row numbers from a Google Sheet.
    """

    def __init__(self, sheet_client):
        """
        Initializes the SheetService with the Google Sheets client.

        Args:
            sheet_client: An authenticated gspread client.
        """
        self.sheet_client = sheet_client

    def get_dates(self, sheet_id, sheet_name, column_name):
        """
        Retrieves a specific column from a Google Sheet, returning the formatted dates along with their row numbers.

        Args:
            sheet_id (str): The Google Sheet ID.
            sheet_name (str): The worksheet (tab) name within the sheet.
            column_name (str): The column name to retrieve (assumed to contain dates).

        Returns:
            JSON response containing formatted dates and their row numbers.
        """
        try:
            # Open the Google Sheet by ID and worksheet name
            sheet = self.sheet_client.open_by_key(
                sheet_id).worksheet(sheet_name)

            # Get the headers (first row) to determine column index
            headers = sheet.row_values(1)

            if column_name not in headers:
                logging.warning(f"Column '{column_name}' not found")
                return {"error": f"Column '{column_name}' not found"}, 404

            # Find the index of the specified column
            # Convert to 1-based index
            col_index = headers.index(column_name) + 1

            # Get column values (skip header row)
            column_values = sheet.col_values(col_index)[1:]

            # Process dates
            row_data = {}
            # Start from row 2 (after headers)
            for row_num, value in enumerate(column_values, start=2):
                if value:  # If the value is not empty
                    row_data[row_num] = {
                        "row": row_num,
                        column_name: self._format_dates(value)
                    }

            # Ensure the result is a dictionary with the 'data' key
            return {"data": list(row_data.values())}

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Sheet with ID '{sheet_id}' not found.")
            return {"error": f"Sheet with ID '{sheet_id}' not found"}, 404

        except gspread.exceptions.WorksheetNotFound:
            logging.error(
                f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'.")
            return {"error": f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'"}, 404

        except Exception as e:
            logging.error(f"Error retrieving column '{column_name}': {str(e)}")
            return {"error": "Internal server error"}, 500

    def compare_and_update_rates(self, sheet_data, rates_data):
        """
        Compares dates from Google Sheets with the rates from `get_rates()` and updates the sheet data.

        Args:
            sheet_data (dict): Data from Google Sheets (output of get_values()).
            rates_data (list): Data from `get_rates()` (list of rates with 'date', 'source', and 'value_sell').

        Returns:
            dict: The updated sheet data with COTIZACIÓN OFICIAL and COTIZACIÓN BLUE filled in.
        """
        # Create a dictionary of rates by date and source
        rates_dict = {}
        for rate in rates_data:
            if rate["date"] not in rates_dict:
                rates_dict[rate["date"]] = {}
            rates_dict[rate["date"]][rate["source"]] = rate["value_sell"]

        # Iterate over sheet data and update rates
        for row in sheet_data["data"]:
            sheet_date = row.get("FECHA DE INGRESO")

            # Check if the date exists in the rates dictionary
            if sheet_date in rates_dict:
                if "Oficial" in rates_dict[sheet_date]:
                    row["COTIZACIÓN OFICIAL"] = rates_dict[sheet_date]["Oficial"]
                if "Blue" in rates_dict[sheet_date]:
                    row["COTIZACIÓN BLUE"] = rates_dict[sheet_date]["Blue"]

        return sheet_data  # Return updated data

    def write_updated_rates(self, sheet_id, sheet_name, updated_data):
        """
        Writes updated exchange rates into Google Sheets.

        Args:
            sheet_id (str): The Google Sheet ID.
            sheet_name (str): The worksheet name inside the sheet.
            updated_data (dict): The updated data with new exchange rates.

        Returns:
            dict: Success or failure message.
        """
        try:
            # Open the Google Sheet by ID and worksheet name
            sheet = self.sheet_client.open_by_key(
                sheet_id).worksheet(sheet_name)

            # Get headers to find column indices
            headers = sheet.row_values(1)
            col_oficial = headers.index(
                "COTIZACIÓN OFICIAL") + 1 if "COTIZACIÓN OFICIAL" in headers else None
            col_blue = headers.index("COTIZACIÓN BLUE") + \
                1 if "COTIZACIÓN BLUE" in headers else None

            if not col_oficial and not col_blue:
                return {"error": "No target columns (COTIZACIÓN OFICIAL / COTIZACIÓN BLUE) found in the sheet"}

            batch_updates = []
            for row in updated_data["data"]:
                row_num = row["row"]

                if col_oficial and "COTIZACIÓN OFICIAL" in row:
                    batch_updates.append({
                        "range": f"{gspread.utils.rowcol_to_a1(row_num, col_oficial)}",
                        "values": [[row["COTIZACIÓN OFICIAL"]]]
                    })

                if col_blue and "COTIZACIÓN BLUE" in row:
                    batch_updates.append({
                        "range": f"{gspread.utils.rowcol_to_a1(row_num, col_blue)}",
                        "values": [[row["COTIZACIÓN BLUE"]]]
                    })

            # Perform batch update
            if batch_updates:
                sheet.batch_update(batch_updates, value_input_option="RAW")
                return {"message": f"Updated {len(batch_updates)} rows successfully."}
            else:
                return {"message": "No updates were needed."}

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Sheet with ID '{sheet_id}' not found.")
            return {"error": f"Sheet with ID '{sheet_id}' not found"}

        except gspread.exceptions.WorksheetNotFound:
            logging.error(
                f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'.")
            return {"error": f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'"}

        except Exception as e:
            logging.error(f"Error writing updated rates: {str(e)}")
            return {"error": "Internal server error"}

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
