"""
Configuration loading for A2A Triage Service
"""
import os
import logging

logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.info("python-dotenv not available, using system environment variables")
    except Exception as e:
        logger.warning(f"Failed to load .env file: {e}")


def get_triage_config():
    """Load and validate triage API configuration"""
    required_vars = [
        'TRIAGE_APP_ID',
        'TRIAGE_APP_KEY',
        'TRIAGE_INSTANCE_ID',
        'TRIAGE_TOKEN_URL',
        'TRIAGE_BASE_URL'
    ]
    
    config = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        config[var.lower()] = value
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("Triage API configuration loaded successfully")
    return config