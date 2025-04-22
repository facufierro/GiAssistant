from dataclasses import dataclass


@dataclass
class Sheet:
    worksheet_id: str
    sheet_name: str
    date_column: str
    rate_column: str
    rate_type: str  # "Oficial" or "Blue"
