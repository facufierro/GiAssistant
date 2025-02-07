import gspread
from google.oauth2.service_account import Credentials


def get_sheet_client():
    """
    Initializes and returns a Google Sheets client.

    Returns:
        gspread.Client: Authenticated Google Sheets client.
    """
    creds = Credentials.from_service_account_file(
        "gihelper-ecd24ac830f8.json",  # Path to your service account key file
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)
