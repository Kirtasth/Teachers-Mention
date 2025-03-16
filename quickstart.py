import os.path
import sys

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.

SAMPLE_RANGE_NAME = "A1:Z3000"

if getattr(sys, 'frozen', False):
  token_path = os.path.join(sys._MEIPASS, 'token.json')
  credentials_path = os.path.join(sys._MEIPASS, 'credentials.json')
else:
  token_path = Path(__file__).parent / "token.json"
  credentials_path = Path(__file__).parent / "credentials.json"

SAMPLE_SPREADSHEET_ID = os.getenv("SHEETS_ID")

def get_teachers_data_from_google_sheets() -> list[str]:
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          credentials_path, SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(token_path, "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()  
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values : list[str] = result.get("values", [])

    if not values:      
      return None
        
    return values

    
  except HttpError as err:    
    return None

