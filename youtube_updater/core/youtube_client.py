from typing import Optional, Dict, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from ..exceptions.custom_exceptions import YouTubeAPIError
from .interfaces import IYouTubeClient

class YouTubeClient(IYouTubeClient):
    """Handles all YouTube API interactions."""
    
    def __init__(self, credentials: Credentials):
        """Initialize the YouTube client.
        
        Args:
            credentials: Google OAuth2 credentials
        """
        self.youtube = build("youtube", "v3", credentials=credentials)
        self.channel_id = None
    
    def get_channel_id(self) -> str:
        """Get the authenticated user's channel ID.
        
        Returns:
            str: Channel ID
            
        Raises:
            YouTubeAPIError: If channel ID cannot be retrieved
        """
        try:
            request = self.youtube.channels().list(part="id", mine=True)
            response = request.execute()
            
            if not response.get("items"):
                raise YouTubeAPIError("Could not retrieve channel ID")
                
            self.channel_id = response["items"][0]["id"]
            return self.channel_id
            
        except Exception as e:
            raise YouTubeAPIError(f"Error getting channel ID: {str(e)}")
    
    def get_live_stream_info(self) -> Dict[str, Any]:
        """Get information about the current live stream.
        
        Returns:
            Dict containing live stream information including:
            - is_live (bool)
            - video_id (str, optional)
            - title (str, optional)
            
        Raises:
            YouTubeAPIError: If live stream info cannot be retrieved
        """
        if not self.channel_id:
            self.get_channel_id()
            
        try:
            # First try to get active broadcasts
            request = self.youtube.liveBroadcasts().list(
                part="snippet,status",
                broadcastStatus="active",
                mine=True
            )
            response = request.execute()
            
            if response.get("items"):
                broadcast = response["items"][0]
                return {
                    "is_live": True,
                    "video_id": broadcast["id"],
                    "title": broadcast["snippet"]["title"]
                }
            
            # If no active broadcasts, check for upcoming broadcasts
            request = self.youtube.liveBroadcasts().list(
                part="snippet,status",
                broadcastStatus="upcoming",
                mine=True
            )
            response = request.execute()
            
            if response.get("items"):
                broadcast = response["items"][0]
                return {
                    "is_live": True,
                    "video_id": broadcast["id"],
                    "title": broadcast["snippet"]["title"]
                }
            
            return {"is_live": False}
            
        except Exception as e:
            raise YouTubeAPIError(f"Error getting live stream info: {str(e)}")
    
    def update_video_title(self, video_id: str, new_title: str) -> None:
        """Update the title of a video.
        
        Args:
            video_id: ID of the video to update
            new_title: New title for the video
            
        Raises:
            YouTubeAPIError: If title update fails
        """
        try:
            # Get current video details
            video_request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response.get("items"):
                raise YouTubeAPIError("Could not retrieve video details")
            
            # Update the title
            snippet = video_response["items"][0]["snippet"]
            snippet["title"] = new_title
            
            update_request = self.youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": snippet
                }
            )
            update_request.execute()
            
        except Exception as e:
            raise YouTubeAPIError(f"Error updating video title: {str(e)}") 