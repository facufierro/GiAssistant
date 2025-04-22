import logging
import io
from flask import Blueprint, render_template_string
from src.services.rates_service import RatesService
from src.services.sheet_service import SheetService
from src.clients.sheets_client import get_sheet_client
from src.models.sheet import Sheet

rates_bp = Blueprint("rates", __name__)
rates_service = RatesService()
sheet_service = SheetService(get_sheet_client())


class InMemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_output = io.StringIO()

    def emit(self, record):
        self.log_output.write(self.format(record) + "\n")

    def get_logs(self):
        return self.log_output.getvalue()


@rates_bp.route("/get_rates", methods=["GET"])
def get_all_rates_and_append():
    log_handler = InMemoryLogHandler()
    log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(log_handler)

    try:
        all_rates = rates_service.get_rates()
        if not all_rates:
            raise Exception("Could not fetch rates from Bluelytics API.")

        # Group by date
        rate_map = {}
        for rate in all_rates:
            date = rate["date"]
            if date not in rate_map:
                rate_map[date] = {}
            rate_map[date][rate["source"]] = rate["value_sell"]

        # Build rows: FECHA, BLUE, OFICIAL
        rows = []
        for date, sources in sorted(rate_map.items()):
            blue = sources.get("Blue", "")
            oficial = sources.get("Oficial", "")
            rows.append([date, blue, oficial])

        if not rows:
            raise Exception("No data rows to append.")

        # Sheet config
        sheet = Sheet(
            worksheet_id="1OmXgQWSe3bg0byWuesE7osBlWFajzKt_QAdb4pbPXf4",
            sheet_name="Cotiz USD blue",
            date_column="FECHA",
            rate_column="BLUE",  # <- just a dummy for compatibility
            rate_type="",        # <- not needed here
        )

        result = sheet_service.append_custom_rates(sheet, rows, expected_headers=["FECHA", "BLUE", "OFICIAL"])

    except Exception as e:
        result = {"error": str(e)}
        logging.error(f"[ERROR] Failed to update rate history: {e}")

    logging.getLogger().removeHandler(log_handler)
    logs = log_handler.get_logs()

    return render_template_string("""
        <html><head><title>Rate Sheet Update</title>
        <style>
            body { font-family: monospace; background: #f4f4f4; padding: 20px; }
            pre { background: #000; color: #0f0; padding: 20px; overflow-x: auto; max-height: 400px; }
            h1 { color: #333; }
        </style></head>
        <body>
            <h1>✅ Full Rate Sheet Update</h1>
            <p><strong>Status:</strong> {{ result.message or result.error }}</p>
            <h2>📜 Logs</h2>
            <pre>{{ logs }}</pre>
        </body></html>
    """, result=result, logs=logs)
