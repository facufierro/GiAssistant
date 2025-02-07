import requests


class RatesService:
    """Service for fetching exchange rate data."""

    def __init__(self):
        self.url = "https://api.bluelytics.com.ar/v2/evolution.json"

    def get_rates(self):
        """Fetch all exchange rate data from the API."""
        response = requests.get(self.url)
        return response.json() if response.status_code == 200 else None

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
