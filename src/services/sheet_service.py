import gspread
import logging
from flask import jsonify
from datetime import datetime
import re


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

    def get_dates(self, sheet_id, sheet_name, column_ingreso, column_venta):
        """
        Retrieves dates from a Google Sheet. If 'FECHA DE INGRESO' is empty, it uses 'FECHA DE VENTA' instead.

        Args:
            sheet_id (str): The Google Sheet ID.
            sheet_name (str): The worksheet (tab) name.
            column_ingreso (str): The column name for 'FECHA DE INGRESO'.
            column_venta (str): The column name for 'FECHA DE VENTA'.

        Returns:
            dict: {
                "data": [...],          # List of valid rows
                "invalid_data": [...]   # List of invalid rows
            }
        """
        self.invalid_dates = []  # Reset storage for invalid values

        try:
            sheet = self.sheet_client.open_by_key(
                sheet_id).worksheet(sheet_name)
            headers = sheet.row_values(1)

            # Ensure both columns exist
            if column_ingreso not in headers or column_venta not in headers:
                logging.warning(
                    f"Columns '{column_ingreso}' or '{column_venta}' not found")
                # ✅ Ensure dictionary return
                return {"data": [], "invalid_data": []}

            col_ingreso_index = headers.index(column_ingreso) + 1
            col_venta_index = headers.index(column_venta) + 1

            # Retrieve all column values (skip header row)
            column_ingreso_values = sheet.col_values(col_ingreso_index)[1:]
            column_venta_values = sheet.col_values(col_venta_index)[1:]

            row_data = []
            for row_num, (ingreso_value, venta_value) in enumerate(zip(column_ingreso_values, column_venta_values), start=2):
                formatted_ingreso = self._format_dates(
                    ingreso_value, row_num) if ingreso_value.strip() else None
                formatted_venta = self._format_dates(
                    venta_value, row_num) if venta_value.strip() else None

                # If 'FECHA DE INGRESO' is empty, use 'FECHA DE VENTA'
                final_date = formatted_ingreso if formatted_ingreso else formatted_venta

                if final_date:  # ✅ Add only valid dates
                    row_data.append({
                        "row": row_num,
                        column_ingreso: final_date
                    })
                else:
                    self.invalid_dates.append(
                        {"row": row_num, "value": f"'{ingreso_value}' and '{venta_value}'"})

            # ✅ Print all invalid values AFTER processing
            if self.invalid_dates:
                print("\nInvalid Date Entries Found:")
                for entry in self.invalid_dates:
                    print(f"Row {entry['row']}: {entry['value']}")

            return {  # ✅ Ensure it always returns a dictionary
                "data": row_data,  # ✅ List of valid rows
                "invalid_data": self.invalid_dates  # ✅ List of invalid rows
            }

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Sheet with ID '{sheet_id}' not found.")
            # ✅ Always return a dictionary
            return {"data": [], "invalid_data": []}

        except gspread.exceptions.WorksheetNotFound:
            logging.error(
                f"Worksheet '{sheet_name}' not found in sheet '{sheet_id}'.")
            return {"data": [], "invalid_data": []}

        except Exception as e:
            logging.error(
                f"Error retrieving column '{column_ingreso}': {str(e)}")
            # ✅ Ensure consistent output
            return {"data": [], "invalid_data": []}

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

        # example element in rates_dict: {'2021-01-01': {'Oficial': 90.0, 'Blue': 150.0}}

        # Iterate over sheet data and update rates
        for row in sheet_data["data"]:
            fecha_venta = row.get("FECHA DE VENTA")
            # print the first row of the sheet data
            fecha_ingreso = row.get("FECHA DE INGRESO")
            # Check if the date exists in the rates dictionary
            if fecha_ingreso in rates_dict:
                if "Oficial" in rates_dict[fecha_ingreso]:
                    row["COTIZACIÓN OFICIAL"] = rates_dict[fecha_ingreso]["Oficial"]
                if "Blue" in rates_dict[fecha_ingreso]:
                    row["COTIZACIÓN BLUE"] = rates_dict[fecha_ingreso]["Blue"]
            else:
                if fecha_venta in rates_dict:
                    if "Oficial" in rates_dict[fecha_venta]:
                        row["COTIZACIÓN OFICIAL"] = rates_dict[fecha_venta]["Oficial"]
                    if "Blue" in rates_dict[fecha_venta]:
                        row["COTIZACIÓN BLUE"] = rates_dict[fecha_venta]["Blue"]

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

    def _format_dates(self, value, row_num):
        """
        Converts a date from 'DD/Mon/YYYY' or 'DD/M/YYYY' to 'YYYY-MM-DD' format.

        Args:
            value (str): The cell value from the Google Sheet.
            row_num (int): The row number of the value.

        Returns:
            str: The converted date in 'YYYY-MM-DD' format, or None if empty.
        """

        if not isinstance(value, str) or not value.strip():  # ✅ If empty, return None
            return None

        # Remove unexpected characters (e.g., commas, extra spaces)
        value = re.sub(r"[^\w/]", "", value).strip()

        if "/" not in value:
            logging.warning(
                f"Skipping invalid date value at row {row_num}: {value}")
            self.invalid_dates.append({"row": row_num, "value": value})
            return None  # Skip invalid non-date values

        try:
            # Try 'DD/Mon/YYYY' format first
            return datetime.strptime(value, "%d/%b/%Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                # Try 'DD/M/YYYY' format where months are numbers
                return datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                logging.warning(
                    f"Skipping invalid date format at row {row_num}: {value}")
                self.invalid_dates.append({"row": row_num, "value": value})
                return None  # Skip invalid values
