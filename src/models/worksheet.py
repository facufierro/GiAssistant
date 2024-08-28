# path: src/models/worksheet.py

import logging


class Worksheet:
    def __init__(self, gspread_worksheet):
        self.gspread_worksheet = gspread_worksheet
        self.title = gspread_worksheet.title

    def get_column(self, column_name):
        """
        Get all values from the specified column by name.
        """
        try:
            headers = self.gspread_worksheet.row_values(1)
            col_index = headers.index(column_name) + 1
            column_values = self.gspread_worksheet.col_values(col_index)
            logging.info(f"Successfully retrieved column '{column_name}' values.")
            return column_values[1:]  # Skip header
        except ValueError:
            logging.error(f"Column '{column_name}' not found.")
            return None

    def get_cell(self, row, col):
        """
        Get the value of a specific cell.
        """
        return self.gspread_worksheet.cell(row, col).value

    def update_cell(self, row, col, value):
        """
        Update the value of a specific cell.
        """
        self.gspread_worksheet.update_cell(row, col, value)
        logging.info(f"Cell at row {row}, column {col} updated successfully.")

    def column(self, column_name):
        """
        Shortcut method to access a column.
        """
        return self.get_column(column_name)
