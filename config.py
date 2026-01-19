"""
Configuration settings for the Subconscious Voice Agent Demo.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# API Configuration
# =============================================================================

SUBCONSCIOUS_API_KEY = os.getenv("SUBCONSCIOUS_API_KEY", "")
SUBCONSCIOUS_BASE_URL = "https://api.subconscious.dev/v1"
DEFAULT_ENGINE = os.getenv("SUBCONSCIOUS_ENGINE", "tim-large")


# =============================================================================
# Flask Configuration
# =============================================================================

class Config:
    """Flask application configuration."""
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "5001"))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
