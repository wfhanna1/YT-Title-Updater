class YouTubeUpdaterError(Exception):
    """Base exception class for YouTube Title Updater."""
    pass

class YouTubeAPIError(YouTubeUpdaterError):
    """Exception raised for YouTube API related errors."""
    pass

class AuthenticationError(YouTubeUpdaterError):
    """Exception raised for authentication related errors."""
    pass

class TitleManagerError(YouTubeUpdaterError):
    """Exception raised for title management related errors."""
    pass

class ConfigError(YouTubeUpdaterError):
    """Exception raised for configuration related errors."""
    pass 