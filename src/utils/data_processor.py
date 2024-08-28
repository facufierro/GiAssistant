# path: src/utils/data_processor.py
import logging
from datetime import datetime


class DataProcessor:
    @staticmethod
    def parse_date(fecha):
        if fecha.strip() and "/" in fecha:
            try:
                return datetime.strptime(fecha, "%d/%m/%Y").strftime('%Y-%m-%d')
            except ValueError as e:
                logging.error(f"Error processing date '{fecha}': {e}")
        return None
