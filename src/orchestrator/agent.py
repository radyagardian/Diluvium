import os
import logging
from google import genai
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("Diluvium.Orchestrator")

load_dotenv()

class GeminiOrchestrator:
    """
    Manages the connection to Google AI Studio (Gemini 3 Flash).
    Will eventually connect to the FastMCP server to execute tools.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = "gemini-3-flash-preview"
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY not found in .env file.")

    def check_connection(self) -> dict:
        """Returns the current status of the Gemini API connection."""
        if not self.api_key:
            return {"status": "Offline (Missing API Key)", "is_connected": False}
        if not self.client:
            return {"status": "Offline (Client Error)", "is_connected": False}
        
        return {"status": "Online (Gemini 3 Flash)", "is_connected": True}

# Singleton instance to be imported by other modules
orchestrator = GeminiOrchestrator()