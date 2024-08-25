import logging
from src.clients.bluelytics_client import BluelyticsClient
from src.clients.google_sheets_client import GoogleSheetClient
from src.services.sheet_service import SheetService
from src.utils.data_processor import DataProcessor
def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize API Clients
    google_sheet_client = GoogleSheetClient(
        sheet_key="1M3Ulqna30dADDj-0ycJghQYUkv5xNGYaezw73uBivcM",
        sheet_name="ventas-dev",
        credentials_file="gihelper-ecd24ac830f8.json"
    )
    
    bluelytics_client = BluelyticsClient(base_url="https://api.bluelytics.com.ar/v2")

    # Initialize Data Processor
    data_processor = DataProcessor()

    # Initialize Sheet Service
    sheet_service = SheetService(
        sheet_client=google_sheet_client,
        data_processor=data_processor,
        api_client=bluelytics_client
    )

    # Update "COTIZACIÓN OFICIAL" based on "FECHA DE VENTA"
    sheet_service.update_rates(
        date_column_name="FECHA DE VENTA",
        target_column_name="COTIZACIÓN OFICIAL",
        rate_type="oficial"
    )

    # Update "COTIZACIÓN BLUE" based on "FECHA DE INGRESO"
    sheet_service.update_rates(
        date_column_name="FECHA DE INGRESO",
        target_column_name="COTIZACIÓN BLUE",
        rate_type="blue"
    )

if __name__ == "__main__":
    main()
