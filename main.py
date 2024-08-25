import requests
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime


def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Error: No data available for the URL {url}. (Status Code: 404)")
    else:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
    return None


def get_rate(date, rate_type):
    url = f'https://api.bluelytics.com.ar/v2/historical?day={date}'
    data = fetch_data(url)
    if data:
        try:
            rate = str(data[rate_type]['value_sell'])
            return rate
        except KeyError as e:
            print(f"Error: Rate type '{rate_type}' not available or improperly formatted data for the given date {date}.")
        return None


def get_column_values(sheet, column_name):
    headers = sheet.row_values(1)
    try:
        col_index = headers.index(column_name) + 1
        column_values = sheet.col_values(col_index)
        return {row_num: value for row_num, value in enumerate(column_values[1:], start=2)}, col_index
    except ValueError:
        print(f"Error: Column '{column_name}' not found.")
        return None, None


def parse_date(fecha):
    if fecha.strip() and "/" in fecha:
        try:
            return datetime.strptime(fecha, "%d/%m/%Y").strftime('%Y-%m-%d')
        except ValueError as e:
            print(f"Error processing date '{fecha}': {e}")
    return None


def process_sheet(sheet_key, sheet_name, credentials_file):
    sheet = initialize_sheet(sheet_key, sheet_name, credentials_file)
    if not sheet:
        return

    # Get relevant column values
    fecha_venta, _ = get_column_values(sheet, "FECHA DE VENTA")
    fecha_ingreso, _ = get_column_values(sheet, "FECHA DE INGRESO")
    _, cotizacion_column_index = get_column_values(sheet, "COTIZACIÓN OFICIAL")
    _, cotizacion_blue_column_index = get_column_values(sheet, "COTIZACIÓN BLUE")

    if fecha_venta is None or fecha_ingreso is None or cotizacion_column_index is None or cotizacion_blue_column_index is None:
        print(f"Error: Required columns not found in the sheet.")
        return

    official_rates_to_update = []
    blue_rates_to_update = []

    # Process "FECHA DE VENTA" for "COTIZACIÓN OFICIAL"
    for row_num, fecha in fecha_venta.items():
        date_str = parse_date(fecha)
        if date_str:
            rate = get_rate(date_str, "oficial")
            if rate:
                official_rates_to_update.append([rate])

    # Process "FECHA DE INGRESO" for "COTIZACIÓN BLUE"
    for row_num, fecha in fecha_ingreso.items():
        date_str = parse_date(fecha)
        if date_str:
            blue_rate = get_rate(date_str, "blue")
            if blue_rate:
                blue_rates_to_update.append([blue_rate])

    # Update "COTIZACIÓN OFICIAL"
    if official_rates_to_update:
        range_start = 2
        range_end = range_start + len(official_rates_to_update) - 1
        range_name = f"{gspread.utils.rowcol_to_a1(range_start, cotizacion_column_index)}:{gspread.utils.rowcol_to_a1(range_end, cotizacion_column_index)}"
        sheet.update(range_name, official_rates_to_update)
        print("COTIZACIÓN OFICIAL update completed.")  # Confirm completion

    # Update "COTIZACIÓN BLUE"
    if blue_rates_to_update:
        range_start = 2
        range_end = range_start + len(blue_rates_to_update) - 1
        range_name = f"{gspread.utils.rowcol_to_a1(range_start, cotizacion_blue_column_index)}:{gspread.utils.rowcol_to_a1(range_end, cotizacion_blue_column_index)}"
        sheet.update(range_name, blue_rates_to_update)
        print("COTIZACIÓN BLUE update completed.")  # Confirm completion


# Function to initialize and authorize the Google Sheet


def initialize_sheet(sheet_key, sheet_name, credentials_file):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_key).worksheet(sheet_name)


if __name__ == "__main__":
    process_sheet("1M3Ulqna30dADDj-0ycJghQYUkv5xNGYaezw73uBivcM", "ventas-dev", "gihelper-ecd24ac830f8.json")
