# path: clients/bluelytics_client.py
import logging
import requests


class BlualyticsClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_data(self, endpoint):
        url = f'{self.base_url}/{endpoint}'
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logging.error(f"An error occurred: {err}")
        return None

    def get_rate(self, date, rate_type):
        endpoint = f'historical?day={date}'
        data = self.fetch_data(endpoint)
        if data:
            try:
                return str(data[rate_type]['value_sell'])
            except KeyError:
                logging.error(f"Rate type '{rate_type}' not available for the given date {date}.")
        return None
