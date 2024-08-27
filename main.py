import logging
from src.clients.bluelytics_client import BluelyticsClient
from src.clients.google_sheets_client import GoogleSheetClient
from src.services.sheet_service import SheetService
from src.utils.data_processor import DataProcessor
from flask import Flask, jsonify

app = Flask(__name__)


def main():
    try:
        # Setup logging
        logging.basicConfig(level=logging.INFO)

        # Initialize API Clients
        logging.info("Initializing Google Sheets client.")
        google_sheet_client = GoogleSheetClient(
            sheet_key="1M3Ulqna30dADDj-0ycJghQYUkv5xNGYaezw73uBivcM",
            sheet_name="Ventas",
            credentials_file="gihelper-ecd24ac830f8.json"
        )

        logging.info("Initializing Bluelytics API client.")
        bluelytics_client = BluelyticsClient(base_url="https://api.bluelytics.com.ar/v2")

        # Initialize Data Processor
        logging.info("Initializing Data Processor.")
        data_processor = DataProcessor()

        # Initialize Sheet Service
        logging.info("Initializing Sheet Service.")
        sheet_service = SheetService(
            sheet_client=google_sheet_client,
            data_processor=data_processor,
            api_client=bluelytics_client
        )

        # Update "COTIZACIÓN OFICIAL" based on "FECHA DE VENTA"
        logging.info("Updating COTIZACIÓN OFICIAL.")
        sheet_service.update_rates(
            date_column_name="FECHA DE VENTA",
            target_column_name="COTIZACIÓN OFICIAL",
            rate_type="oficial"
        )

        # Update "COTIZACIÓN BLUE" based on "FECHA DE INGRESO"
        logging.info("Updating COTIZACIÓN BLUE.")
        sheet_service.update_rates(
            date_column_name="FECHA DE INGRESO",
            target_column_name="COTIZACIÓN BLUE",
            rate_type="blue"
        )

        logging.info("Rates updated successfully.")
        return True

    except Exception as e:
        logging.error(f"An error occurred in main(): {e}")
        return False


@app.route('/')
def home():
    # Run the main logic when the home page is accessed
    success = main()
    if success:
        return jsonify({"message": "Rates updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update rates"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
