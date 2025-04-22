from datetime import datetime, timedelta
import gspread
import logging
import traceback
from dateutil import parser
from src.models.sheet import Sheet
from bisect import bisect_left


class SheetService:
    def __init__(self, sheet_client):
        self.client = sheet_client

    def update_sheet(self, sheet: Sheet, rates: list) -> dict:
        rows = self._get_valid_rows(sheet)
        if not rows["data"]:
            return {"message": "No valid dates found.", "invalid_data": rows["invalid_data"]}

        updated = self._apply_rates(rows["data"], rates, sheet)
        write_result = self._write_rates(sheet, updated)
        return {**write_result, "invalid_data": rows["invalid_data"], "matched_rows": len(updated)}

    def _get_valid_rows(self, sheet: Sheet) -> dict:
        try:
            ws = self.client.open_by_key(sheet.worksheet_id).worksheet(sheet.sheet_name)
            headers = ws.row_values(1)
            if sheet.date_column not in headers:
                msg = f"Missing date column '{sheet.date_column}'"
                logging.warning(msg)
                return {"data": [], "invalid_data": [], "error": msg}

            idx = headers.index(sheet.date_column) + 1
            values = ws.col_values(idx)[1:]
            valid, invalid = [], []

            for i, val in enumerate(values, start=2):
                date = self._parse_date(val)
                (valid if date else invalid).append(
                    {"row": i, sheet.date_column: date} if date else {"row": i, "value": val}
                )
            return {"data": valid, "invalid_data": invalid}
        except Exception as e:
            logging.error(f"Failed to read sheet '{sheet.sheet_name}': {traceback.format_exc()}")

            return {"data": [], "invalid_data": [], "error": str(e)}

    def _apply_rates(self, data: list, rates: list, sheet: Sheet) -> list:
        rate_map = {r["date"]: r["value_sell"] for r in rates if r["source"] == sheet.rate_type}
        sorted_dates = sorted(rate_map.keys())
        sorted_datetimes = [datetime.strptime(date, "%Y-%m-%d") for date in sorted_dates]

        for row in data:
            original_date = row.get(sheet.date_column)
            matched_date = self._resolve_rate_date(original_date, rate_map)

            if matched_date:
                row[sheet.rate_column] = rate_map[matched_date]
            else:
                row["_missing_rate_for_date"] = original_date

        return data

    def _write_rates(self, sheet: Sheet, data: list) -> dict:
        try:
            ws = self.client.open_by_key(sheet.worksheet_id).worksheet(sheet.sheet_name)
            headers = ws.row_values(1)

            if sheet.rate_column not in headers:
                logging.error(f"[{sheet.sheet_name}] Rate column '{sheet.rate_column}' not found. Headers: {headers}")
                return {"error": f"Rate column '{sheet.rate_column}' not found."}

            col_idx = headers.index(sheet.rate_column) + 1
            updates = []
            skipped = []

            for row in data:
                if sheet.rate_column not in row:
                    reason = "Rate value missing"
                    date = row.get("_missing_rate_for_date", row.get(sheet.date_column, "N/A"))
                    skipped.append((row["row"], reason, date))
                    continue
                value = row[sheet.rate_column]
                if value is None or value == "":
                    skipped.append((row["row"], "Rate value is empty", row.get(sheet.date_column, "N/A")))
                    continue
                updates.append({
                    "range": gspread.utils.rowcol_to_a1(row["row"], col_idx),
                    "values": [[value]]
                })

            if updates:
                ws.batch_update(updates, value_input_option="RAW")
                logging.info(f"[{sheet.sheet_name}] ✅ Wrote {len(updates)} cells.")
            else:
                logging.warning(f"[{sheet.sheet_name}] ⚠️ No updates were made. All rows skipped.")

            for row_num, reason, date in skipped:
                logging.warning(f"[{sheet.sheet_name}] Skipped row {row_num} (Date: {date}) ➜ {reason}")

            return {
                "message": f"Updated {len(updates)} rows." if updates else "No updates were made.",
                "skipped_rows": len(skipped),
                "skipped_reasons": skipped
            }

        except Exception as e:
            msg = f"Error writing to sheet '{sheet.sheet_name}': {e}"
            logging.error(msg)
            return {"error": msg}

    def _parse_date(self, val: str) -> str | None:
        try:
            return parser.parse(val.strip(), dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            return None

    def _resolve_rate_date(self, target: str, rate_map: dict, max_lookback_days: int = 10) -> str | None:
        target_date = datetime.strptime(target, "%Y-%m-%d")
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        if target_date > today:
            target_date = today

        if target_date.weekday() == 5:
            target_date -= timedelta(days=1)
        elif target_date.weekday() == 6:
            target_date -= timedelta(days=2)

        for i in range(max_lookback_days + 1):
            date_str = (target_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if date_str in rate_map:
                return date_str

        return None
