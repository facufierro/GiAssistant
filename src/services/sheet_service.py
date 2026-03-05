from datetime import datetime, timedelta
import gspread
import logging
import traceback
import time
from dateutil import parser
from gspread.exceptions import APIError
from src.models.sheet import Sheet


class SheetService:
    def __init__(self, sheet_client):
        self.client = sheet_client

    def update_sheet(self, sheet: Sheet, rates: list) -> dict:
        rows = self._get_valid_rows(sheet)
        if not rows or not rows.get("data"):
            return {"message": "No valid dates found.", "invalid_data": rows.get("invalid_data", [])}

        updated = self._apply_rates(rows["data"], rates, sheet)
        write_result = self._write_rates(sheet, updated)
        return {**write_result, "invalid_data": rows["invalid_data"], "matched_rows": len(updated)}

    def _retry_gspread_call(self, func, *args, retries=5, delay=10, **kwargs):
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if "429" in str(e):
                    wait = delay * (attempt + 1)
                    logging.warning(f"Rate limit hit. Retrying in {wait}s... (attempt {attempt + 1})")
                    time.sleep(wait)
                else:
                    raise
        raise Exception(f"Rate limit retry failed after {retries} attempts.")

    def _get_valid_rows(self, sheet: Sheet) -> dict:
        try:
            ws = self.client.open_by_key(sheet.worksheet_id).worksheet(sheet.sheet_name)
            headers = self._retry_gspread_call(ws.row_values, 1)

            if sheet.date_column not in headers:
                msg = f"Missing required column: {sheet.date_column}"
                logging.warning(msg)
                return {"data": [], "invalid_data": [], "error": msg}

            date_idx = headers.index(sheet.date_column) + 1
            dates = self._retry_gspread_call(ws.col_values, date_idx)[1:]

            currencies = []
            currency_idx = None
            if sheet.currency_column and sheet.currency_column in headers:
                currency_idx = headers.index(sheet.currency_column) + 1
                currencies = self._retry_gspread_call(ws.col_values, currency_idx)[1:]
            else:
                currencies = [None] * len(dates)

            valid, invalid = [], []
            for i, (date_val, currency_val) in enumerate(zip(dates, currencies), start=2):
                parsed_date = self._parse_date(date_val)
                if parsed_date:
                    row_data = {"row": i, sheet.date_column: parsed_date}
                    if sheet.currency_column:
                        row_data[sheet.currency_column] = currency_val.strip().upper() if currency_val else ""
                    valid.append(row_data)
                else:
                    invalid.append({"row": i, "value": date_val})

            return {"data": valid, "invalid_data": invalid}
        except Exception as e:
            logging.error(f"Failed to read sheet '{sheet.sheet_name}': {traceback.format_exc()}")
            return {"data": [], "invalid_data": [], "error": str(e)}

    def _apply_rates(self, data: list, rates: list, sheet: Sheet) -> list:
        rate_map = {r["date"]: r["value_sell"] for r in rates if r["source"] == sheet.rate_type}

        for row in data:
            if sheet.currency_column:
                currency = row.get(sheet.currency_column, "").upper()
                if currency == "USD":
                    row[sheet.rate_column] = 1
                    continue

            original_date = row.get(sheet.date_column)
            matched_date = self._resolve_rate_date(original_date, rate_map)

            if matched_date:
                row[sheet.rate_column] = rate_map[matched_date]
            else:
                row["_missing_rate_for_date"] = original_date
                logging.warning(
                    f"[{sheet.sheet_name}] Row {row.get('row')} – could not resolve rate for date '{original_date}'"
                )

        return data

    def _write_rates(self, sheet: Sheet, data: list) -> dict:
        try:
            ws = self.client.open_by_key(sheet.worksheet_id).worksheet(sheet.sheet_name)
            headers = self._retry_gspread_call(ws.row_values, 1)

            if sheet.rate_column not in headers:
                logging.error(f"[{sheet.sheet_name}] Rate column '{sheet.rate_column}' not found. Headers: {headers}")
                return {"error": f"Rate column '{sheet.rate_column}' not found."}

            col_idx = headers.index(sheet.rate_column) + 1
            updates, skipped = [], []

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
                self._retry_gspread_call(ws.batch_update, updates, value_input_option="RAW")
                logging.info(f"[{sheet.sheet_name}] ✅ Wrote {len(updates)} cells.")
            else:
                logging.warning(f"[{sheet.sheet_name}] ⚠️ No updates were made. All rows skipped.")

            if skipped:
                logging.info(f"[{sheet.sheet_name}] ⏭️ Skipped {len(skipped)} rows due to missing or invalid rates.")
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
        try:
            target_date = datetime.strptime(target, "%Y-%m-%d")
        except ValueError:
            logging.warning(f"⚠️ Skipping rate resolution for malformed date string: '{target}'")
            return None

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

    def append_custom_rates(self, sheet: Sheet, rows: list, expected_headers: list) -> dict:
        try:
            ws = self.client.open_by_key(sheet.worksheet_id).worksheet(sheet.sheet_name)

            # Validate headers
            headers = self._retry_gspread_call(ws.row_values, 1)
            missing = [h for h in expected_headers if h not in headers]
            if missing:
                return {"error": f"Missing columns: {missing}"}

            # Sort rows descending by date
            rows.sort(key=lambda x: x[0], reverse=True)

            # Resize if needed
            total_rows_needed = len(rows) + 1  # +1 for header
            if total_rows_needed > ws.row_count:
                self._retry_gspread_call(ws.resize, total_rows_needed)

            # Clear all below header
            end_col = len(expected_headers)
            clear_range = f"A2:{chr(64+end_col)}{ws.row_count}"
            self._retry_gspread_call(ws.batch_clear, [clear_range])

            # Write new data starting from A2
            self._retry_gspread_call(ws.update, f"A2", rows)

            logging.info(f"[{sheet.sheet_name}] ✅ Overwrote {len(rows)} rows, newest first.")
            return {"message": f"Overwrote {len(rows)} rate rows."}
        except Exception as e:
            logging.error(f"Error writing combined rate history: {e}")
            return {"error": str(e)}

    def update_missing_sales_rates(self, worksheet_id: str, sheet_name: str, rates: list) -> dict:
        """
        Fills COTIZACIÓN OFICIAL and COTIZACIÓN BLUE for rows that have a FECHA DE VENTA 
        but are missing one or both exchange rates.
        """
        try:
            ws = self.client.open_by_key(worksheet_id).worksheet(sheet_name)
            data = self._retry_gspread_call(ws.get_all_values)
            if not data:
                return {"error": "Sheet is empty"}

            headers = data[0]
            rows = data[1:]

            date_col = "FECHA DE VENTA"
            official_col = "COTIZACIÓN OFICIAL"
            blue_col = "COTIZACIÓN BLUE"

            if date_col not in headers or official_col not in headers or blue_col not in headers:
                logging.error(f"[{sheet_name}] Missing columns. Headers found: {headers}")
                return {"error": f"Required columns missing: {date_col}, {official_col} or {blue_col}"}

            date_idx = headers.index(date_col)
            off_idx = headers.index(official_col)
            blue_idx = headers.index(blue_col)

            official_rates = {r["date"]: r["value_sell"] for r in rates if r["source"] == "Oficial"}
            blue_rates = {r["date"]: r["value_sell"] for r in rates if r["source"] == "Blue"}

            updates = []
            rows_affected = 0

            for i, row in enumerate(rows, start=2):
                date_val = row[date_idx].strip()
                if not date_val:
                    continue

                curr_off = row[off_idx].strip()
                curr_blue = row[blue_idx].strip()

                # Only proceed if at least one rate is missing
                if curr_off and curr_blue:
                    continue

                parsed_date = self._parse_date(date_val)
                if not parsed_date:
                    continue

                # Resolve and queue updates
                match_off = self._resolve_rate_date(parsed_date, official_rates)
                match_blue = self._resolve_rate_date(parsed_date, blue_rates)

                row_updated = False
                if match_off and not curr_off:
                    updates.append({
                        "range": gspread.utils.rowcol_to_a1(i, off_idx + 1),
                        "values": [[official_rates[match_off]]]
                    })
                    row_updated = True

                if match_blue and not curr_blue:
                    updates.append({
                        "range": gspread.utils.rowcol_to_a1(i, blue_idx + 1),
                        "values": [[blue_rates[match_blue]]]
                    })
                    row_updated = True

                if row_updated:
                    rows_affected += 1

            if updates:
                self._retry_gspread_call(ws.batch_update, updates, value_input_option="RAW")
                logging.info(f"[{sheet_name}] ✅ Updated {rows_affected} rows ({len(updates)} cells).")
            else:
                logging.info(f"[{sheet_name}] No missing rates found to update.")

            return {
                "message": f"Updated {rows_affected} rows." if updates else "No updates needed.",
                "total_cells": len(updates)
            }

        except Exception as e:
            msg = f"Error in update_missing_sales_rates for '{sheet_name}': {e}"
            logging.error(msg)
            return {"error": msg}

    def _get_logger(self, sheet_name: str):
        return logging.LoggerAdapter(logging.getLogger(), {"sheet": sheet_name})
