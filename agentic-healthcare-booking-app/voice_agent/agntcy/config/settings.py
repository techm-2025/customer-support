"""
Configuration Settings
"""
import os
from dotenv import load_dotenv

# Try to import audio dependencies
try:
    import speech_recognition as sr
    import pygame
    from gtts import gTTS
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class Settings:
    """Application settings from environment variables"""
    
    def __init__(self):
        load_dotenv()
        
        # LLM Configuration
        self.jwt_token = os.getenv('JWT_TOKEN')
        self.endpoint_url = os.getenv('ENDPOINT_URL')
        self.project_id = os.getenv('PROJECT_ID')
        self.connection_id = os.getenv('CONNECTION_ID')
        
        # Insurance/MCP Configuration
        self.mcp_url = os.getenv('MCP_URL')
        self.insurance_api_key = os.getenv('X_INF_API_KEY')
        
        # A2A Configuration
        self.a2a_service_url = os.getenv('A2A_SERVICE_URL', 'http://localhost:8887')
        self.a2a_message_url = os.getenv('A2A_MESSAGE_URL', self.a2a_service_url)
        self.a2a_api_key = os.getenv('A2A_API_KEY')
        
        # TBAC Configuration
        self.client_agent_api_key = os.getenv('CLIENT_AGENT_API_KEY')
        self.client_agent_id = os.getenv('CLIENT_AGENT_ID')
        self.a2a_service_api_key = os.getenv('A2A_SERVICE_API_KEY')
        self.a2a_service_id = os.getenv('A2A_SERVICE_ID')
        
        # Observability Configuration
        self.otlp_endpoint = os.getenv('OTLP_ENDPOINT', 'http://localhost:4318')
        
        # Audio Configuration
        self.audio_available = AUDIO_AVAILABLE
        
        # Session Configuration
        self.session_dir = os.getenv('SESSION_DIR', 'sessions')
        self.max_turns = int(os.getenv('MAX_TURNS', '50'))
        self.max_errors = int(os.getenv('MAX_ERRORS', '3'))