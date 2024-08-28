# path: src/clients/bluelytics_client.py
import time
import logging
import requests


class BluelyticsClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_data(self, endpoint, retries=5):
        url = f'{self.base_url}/{endpoint}'
        for i in range(retries):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    wait_time = 2 ** i
                    logging.error(f"HTTP error occurred: {http_err}. Retrying in {wait_time} seconds... (Retry {i+1}/{retries})")
                    time.sleep(wait_time)
                else:
                    logging.error(f"HTTP error occurred: {http_err}")
                    break
            except Exception as err:
                logging.error(f"An error occurred: {err}")
                break
        logging.error(f"Failed to fetch data after {retries} retries.")
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
