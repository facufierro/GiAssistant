# path: src/services/rates_service.py
import logging
import gspread
from datetime import datetime
from src.clients.bluelytics_client import BluelyticsClient


class RatesService:
    def __init__(self, spreadsheet, data_processor):
        self.spreadsheet = spreadsheet
        self.data_processor = data_processor

    def update(self, worksheet_title, date_column_name, target_column_name, rate_type):
        worksheet = self.spreadsheet.get_worksheet(worksheet_title)
        if not worksheet:
            logging.error(f"Worksheet '{worksheet_title}' not found.")
            return

        # Get columns
        dates_column = worksheet.get_column(date_column_name)
        target_column_index = worksheet.get_column_index(target_column_name)

        if not dates_column or target_column_index is None:
            logging.error("Required columns not found.")
            return

        # Get rates to update
        rates_to_update = self._get_rates_to_update(dates_column, rate_type)

        # Perform batch update
        if rates_to_update:
            batch_data = []
            for row_num, rate in rates_to_update:
                cell_range = f"{gspread.utils.rowcol_to_a1(row_num, target_column_index)}"
                batch_data.append({
                    "range": cell_range,
                    "values": [[rate]]
                })
            worksheet.batch_update(batch_data)
            logging.info(f"Batch updated {len(rates_to_update)} rows with {rate_type} rates.")

    def _get_rates_to_update(self, dates_column, rate_type):
        """
        Fetch exchange rates for the given dates and rate type using BluelyticsClient's static methods.
        """
        rates_to_update = []
        today = datetime.today().date()

        for row_num, fecha in enumerate(dates_column, start=2):  # Skips header row
            date_str = self.data_processor.parse_date(fecha)
            if date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj > today:
                    date_str = today.strftime("%Y-%m-%d")

                # Now using BluelyticsClient's static method directly
                rate = BluelyticsClient.get_rate(date_str, rate_type)  # Static method call
                if rate:
                    rates_to_update.append((row_num, rate))
                else:
                    logging.warning(f"Could not retrieve rate for {date_str} at row {row_num}.")
        return rates_to_update
