import requests

class RatesService:
    """Service for fetching exchange rate data."""

    def __init__(self):
        self.url = "https://api.bluelytics.com.ar/v2/evolution.json"

    def get_rates(self):
        """Fetch all exchange rate data from the API."""
        response = requests.get(self.url)
        return response.json() if response.status_code == 200 else None

    def filter_rates(self, dates: list, source: str):
        """
        Filters exchange rates for multiple dates based on the specified source.

        Args:
            dates (list): A list of dates to filter by (format: "YYYY-MM-DD").
            source (str): The exchange rate source (e.g., "Oficial", "Blue").

        Returns:
            list: A list of matching exchange rate entries.
        """
        all_rates = self.get_rates()
        if not all_rates:
            return None  # API call failed, return None

        # Normalize source input to lowercase for case-insensitive comparison
        source = source.lower()

        # Filter the list for matching dates and source
        filtered_rates = [
            rate for rate in all_rates
            if rate["date"] in dates and rate["source"].lower() == source
        ]

        return filtered_rates if filtered_rates else None  # Return None if no matches found
