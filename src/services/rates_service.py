# path: src/services/rates_service.py
import os
from dotenv import load_dotenv
from src.clients.bluelytics_client import BluelyticsClient
from src.clients.google_sheets_client import GoogleSheetClient
from src.services.sheet_service import SheetService
from src.utils.data_processor import DataProcessor

load_dotenv()


class RatesService:
    def __init__(self):
        self.google_sheet_client = GoogleSheetClient(
            sheet_key=os.getenv("PREVENTAS_VENTA_2024"),
            sheet_name="Ventas",
            credentials_file="gihelper-ecd24ac830f8.json"
        )

        self.bluelytics_client = BluelyticsClient(base_url="https://api.bluelytics.com.ar/v2")
        self.data_processor = DataProcessor()

        self.sheet_service = SheetService(
            sheet_client=self.google_sheet_client,
            data_processor=self.data_processor,
            api_client=self.bluelytics_client
        )

    def update_rates(self):
        self.sheet_service.update_rates(
            date_column_name="FECHA DE VENTA",
            target_column_name="COTIZACIÓN OFICIAL",
            rate_type="oficial"
        )
        self.sheet_service.update_rates(
            date_column_name="FECHA DE INGRESO",
            target_column_name="COTIZACIÓN BLUE",
            rate_type="blue"
        )
