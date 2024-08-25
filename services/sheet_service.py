# path: services/sheet_service.py
import logging


class SheetService:
    def __init__(self, sheet_client, data_processor, api_client):
        self.sheet_client = sheet_client
        self.data_processor = data_processor
        self.api_client = api_client

    def process_and_update(self):
        # Retrieve relevant column values
        fecha_venta, cotizacion_column_index = self.sheet_client.get_column_values("FECHA DE VENTA")
        fecha_ingreso, cotizacion_blue_column_index = self.sheet_client.get_column_values("FECHA DE INGRESO")

        if fecha_venta is None or fecha_ingreso is None:
            logging.error("Required columns not found in the sheet.")
            return

        official_rates_to_update = []
        blue_rates_to_update = []

        for row_num, fecha in fecha_venta.items():
            date_str = self.data_processor.parse_date(fecha)
            if date_str:
                rate = self.api_client.get_rate(date_str, "oficial")
                if rate:
                    official_rates_to_update.append([rate])
                    logging.debug(f"Added official rate {rate} for row {row_num}.")

        for row_num, fecha in fecha_ingreso.items():
            date_str = self.data_processor.parse_date(fecha)
            if date_str:
                blue_rate = self.api_client.get_rate(date_str, "blue")
                if blue_rate:
                    blue_rates_to_update.append([blue_rate])
                    logging.debug(f"Added blue rate {blue_rate} for row {row_num}.")

        self.sheet_client.update_column(cotizacion_column_index, official_rates_to_update)
        self.sheet_client.update_column(cotizacion_blue_column_index, blue_rates_to_update)
