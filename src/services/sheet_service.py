# path: services/sheet_service.py
import logging
import gspread

class SheetService:
    def __init__(self, sheet_client, data_processor, api_client):
        self.sheet_client = sheet_client
        self.data_processor = data_processor
        self.api_client = api_client

    def update_rates(self, date_column_name, target_column_name, rate_type):
        dates_column, target_column_index = self._get_columns(date_column_name, target_column_name)
        if dates_column is None or target_column_index is None:
            logging.error("Required columns not found in the sheet.")
            return

        rates_to_update = self._get_rates_to_update(dates_column, rate_type)

        if rates_to_update:
            batch_data = []
            for row_num, rate in rates_to_update:
                cell_range = f"{gspread.utils.rowcol_to_a1(row_num, target_column_index)}"
                batch_data.append({
                    "range": cell_range,
                    "values": [[rate]]
                })
            
            # Perform the batch update with valueInputOption to override existing values
            self.sheet_client.sheet.batch_update(
                batch_data,
                value_input_option="RAW"
            )
            logging.info(f"Batch updated {len(rates_to_update)} rows for {rate_type} rates.")





    def _get_columns(self, date_column_name, target_column_name):
        dates_column, _ = self.sheet_client.get_column_values(date_column_name)
        _, target_column_index = self.sheet_client.get_column_values(target_column_name)
        return dates_column, target_column_index

    def _get_rates_to_update(self, dates_column, rate_type):
        rates_to_update = []
        for row_num, fecha in dates_column.items():
            date_str = self.data_processor.parse_date(fecha)
            if date_str:
                rate = self.api_client.get_rate(date_str, rate_type)
                if rate:
                    rates_to_update.append((row_num, rate))  # Store row number with rate
                    logging.debug(f"Added {rate_type} rate {rate} for row {row_num}.")
                else:
                    logging.warning(f"Could not retrieve rate for date {date_str} at row {row_num}.")
        return rates_to_update




