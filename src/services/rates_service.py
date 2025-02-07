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
        Compares dates from Google Sheets with the rates and updates the sheet data.

        Args:
            sheet_data (list): Data from Google Sheets (output of get_dates()["data"]).
            rates_data (list): Data from `get_rates()` (list of rates with 'date', 'source', and 'value_sell').

        Returns:
            dict: The updated sheet data with exchange rates filled in.
        """
        if not isinstance(sheet_data, list):  # ✅ Ensure sheet_data["data"] is a list
            raise TypeError(f"Expected list, got {type(sheet_data)}")

        rates_dict = {}
        for rate in rates_data:
            if rate["date"] not in rates_dict:
                rates_dict[rate["date"]] = {}
            rates_dict[rate["date"]][rate["source"]] = rate["value_sell"]

        for row in sheet_data:  # ✅ Loop safely
            fecha_ingreso = row.get("FECHA DE INGRESO", None)
            fecha_venta = row.get("FECHA DE VENTA", None)

            # Use fecha_venta if fecha_ingreso is missing
            final_date = fecha_ingreso if fecha_ingreso else fecha_venta

            if final_date in rates_dict:
                row["COTIZACIÓN OFICIAL"] = rates_dict[final_date].get(
                    "Oficial", "N/A")
                row["COTIZACIÓN BLUE"] = rates_dict[final_date].get(
                    "Blue", "N/A")

        return {"data": sheet_data}  # ✅ Ensure it returns a dictionary
