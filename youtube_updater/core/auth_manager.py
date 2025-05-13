import os
import pickle
from typing import Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ..exceptions.custom_exceptions import AuthenticationError

class AuthManager:
    """Handles YouTube API authentication."""
    
    SCOPES = ["https://www.googleapis.com/auth/youtube"]
    
    def __init__(self, client_secrets_path: str, token_path: str):
        """Initialize the authentication manager.
        
        Args:
            client_secrets_path: Path to the client secrets JSON file
            token_path: Path to store/load the token pickle file
        """
        self.client_secrets_path = client_secrets_path
        self.token_path = token_path
    
    def get_credentials(self) -> Credentials:
        """Get valid credentials for YouTube API.
        
        Returns:
            Credentials: Valid Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            creds = self._load_credentials()
            if not creds or not creds.valid:
                creds = self._refresh_or_authenticate(creds)
            return creds
            
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file if it exists.
        
        Returns:
            Optional[Credentials]: Loaded credentials or None if file doesn't exist
        """
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                return pickle.load(token)
        return None
    
    def _refresh_or_authenticate(self, creds: Optional[Credentials]) -> Credentials:
        """Refresh existing credentials or authenticate new ones.
        
        Args:
            creds: Existing credentials to refresh, or None for new authentication
            
        Returns:
            Credentials: Refreshed or new credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_path):
                    raise AuthenticationError(
                        f"Client secrets file not found at: {self.client_secrets_path}"
                    )
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_path,
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)
            return creds
            
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}") 