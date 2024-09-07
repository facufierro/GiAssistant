# path: src/models/worksheet.py

from typing import List, Dict, Tuple
from gspread.worksheet import Worksheet as GspreadWorksheet


class Cell:
    def __init__(self, x: int, y: int, value: str):
        self.x = x
        self.y = y
        self.value = value


class Worksheet:
    def __init__(self, gspread_worksheet: GspreadWorksheet):
        self.gspread_worksheet: GspreadWorksheet = gspread_worksheet
        self.title: str = self.get_title()
        self.headers: List[str] = self.get_headers()
        self.cells: Dict[Tuple[int, int], Cell] = self.get_cells()

    def get_title(self) -> str:
        return self.gspread_worksheet.title

    def get_headers(self, header_index: int = 1) -> List[str]:
        return self.gspread_worksheet.row_values(header_index)

    def get_cells(self) -> Dict[Tuple[int, int], Cell]:
        cell_list: List[List[str]] = self.gspread_worksheet.get_all_values()
        cells: Dict[Tuple[int, int], Cell] = {}
        for row_idx, row in enumerate(cell_list[1:], start=2):
            for col_idx, value in enumerate(row, start=1):
                if value:
                    cells[(row_idx, col_idx)] = Cell(x=row_idx, y=col_idx, value=value)
        return cells
