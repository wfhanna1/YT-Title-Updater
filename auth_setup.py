import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube"]
TOKEN_PATH = os.path.expanduser("~/Library/Application Support/yt_title_updater/token.pickle")
SECRETS_PATH = os.path.expanduser("~/Library/Application Support/yt_title_updater/client_secrets.json")

def authenticate():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token_file:
            creds = pickle.load(token_file)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("Token refreshed.")
    else:
        flow = InstalledAppFlow.from_client_secrets_file(SECRETS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)  # This will open a browser window
        print("New token generated.")

    with open(TOKEN_PATH, "wb") as token_file:
        pickle.dump(creds, token_file)
    print(f"Token saved to {TOKEN_PATH}")

if __name__ == "__main__":
    authenticate()