from dataclasses import dataclass
from typing import Optional


@dataclass
class Sheet:
    worksheet_id: str
    sheet_name: str
    date_column: str
    rate_column: str
    rate_type: str
    currency_column: Optional[str] = None
