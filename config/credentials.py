import os
from dotenv import load_dotenv

load_dotenv()

class Credentials:
    # PocketOption credentials from WebSocket trace
    SESSION_TOKEN = os.getenv('SESSION_TOKEN', '')  # Changed from SESSION_ID
    USER_ID = os.getenv('USER_ID', '')  # Added UID from auth payload
    IS_DEMO = int(os.getenv('IS_DEMO', 1))  # Default to Demo (1) as it's more common
    # REMOVED TOURNAMENT_ID - not used by PocketOption
    WS_URL = os.getenv('WS_URL', 'wss://events-po.com/socket.io/?EIO=4&transport=websocket')  # Updated URL
    
    @classmethod
    def validate(cls):
        """Validate credentials for PocketOption"""
        if not cls.SESSION_TOKEN:
            raise ValueError("SESSION_TOKEN is required in environment variables")
        if not cls.USER_ID:
            raise ValueError("USER_ID is required in environment variables")
        # Removed length validation as PocketOption token format may vary
        return True
