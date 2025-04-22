import os
import io
import logging
from flask import Blueprint, render_template_string
from dotenv import load_dotenv
from src.models.sheet import Sheet
from src.services.sheet_service import SheetService
from src.services.rates_service import RatesService
from src.clients.sheets_client import get_sheet_client


class InMemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_output = io.StringIO()

    def emit(self, record):
        self.log_output.write(self.format(record) + "\n")

    def get_logs(self):
        return self.log_output.getvalue()


load_dotenv()
sheets_bp = Blueprint("sheets", __name__)
sheet_service = SheetService(get_sheet_client())
rates_service = RatesService()

SHEETS_TO_UPDATE = [
    Sheet("16GpI2yKovf5sqyeBD42CAMP1W4C2-Ap_tpuoBPBv34s", "Ventas", "FECHA DE INGRESO", "COTIZACIÓN OFICIAL", "Oficial"),
    Sheet("16GpI2yKovf5sqyeBD42CAMP1W4C2-Ap_tpuoBPBv34s", "Ventas", "FECHA DE INGRESO", "COTIZACIÓN BLUE", "Blue"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Selección IT", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Selección", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Employee Experience", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Cap. In Company", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Workshop", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
    Sheet("1oJ_miq5ZI-A28-cyK4gZMXWAP5PdO94nkFOAHYRm4c8", "Otros Ing", "FECHA DE INICIO", "COTIZ", "Blue", "MONEDA"),
]


@sheets_bp.route("/update_sheet", methods=["GET"])
def update_sheet():
    log_handler = InMemoryLogHandler()
    log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(log_handler)

    rates = rates_service.get_rates()
    results = [
        {
            "sheet_name": sheet.sheet_name,
            "rate_column": sheet.rate_column,
            "status": sheet_service.update_sheet(sheet, rates)
        }
        for sheet in SHEETS_TO_UPDATE
    ]

    logging.getLogger().removeHandler(log_handler)
    return render_template_string("""
        <html><head><title>Sheet Update Results</title>
        <style>body { font-family: monospace; background: #f4f4f4; padding: 20px; }
        pre { background: #000; color: #0f0; padding: 20px; overflow-x: auto; max-height: 400px; }
        h1 { color: #333; }</style></head>
        <body>
            <h1>✅ Sheet Update Results</h1>
            {% for r in results %}
                <h2>{{ r.sheet_name }}</h2>
                <p><strong>Status:</strong> {{ r.status.message or r.status.error }}</p>
            {% endfor %}
            <h2>📜 Logs</h2>
            <pre>{{ logs }}</pre>
        </body></html>
    """, results=results, logs=log_handler.get_logs())
