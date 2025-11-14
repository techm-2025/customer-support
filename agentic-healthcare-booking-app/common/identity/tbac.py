"""
TBAC (Task-Based Access Control) Configuration
"""
import os
import logging
from dotenv import load_dotenv

try:
    from identityservice.sdk import IdentityServiceSdk
    TBAC_AVAILABLE = True
except ImportError:
    TBAC_AVAILABLE = False
    logging.warning("identityservice.sdk not available - TBAC disabled")


logger = logging.getLogger(__name__)


class TBAC:
    """TBAC configuration and authorization handler"""
    
    def __init__(self):
        load_dotenv()
        
        # TBAC credentials
        self.client_api_key = os.getenv('CLIENT_AGENT_API_KEY')
        self.client_id = os.getenv('CLIENT_AGENT_ID')
        self.a2a_api_key = os.getenv('A2A_SERVICE_API_KEY')
        self.a2a_id = os.getenv('A2A_SERVICE_ID')
        
        self.client_sdk = None
        self.a2a_sdk = None
        self.client_authorized = False
        self.a2a_authorized = False
        self.client_token = None
        self.a2a_token = None
        
        if TBAC_AVAILABLE:
            self._setup()
    
    def _setup(self):
        """Initialize TBAC SDKs"""
        if not all([self.client_api_key, self.client_id, self.a2a_api_key, self.a2a_id]):
            logger.warning("TBAC Disabled: Missing credentials")
            return
        
        try:
            self.client_sdk = IdentityServiceSdk(api_key=self.client_api_key)
            self.a2a_sdk = IdentityServiceSdk(api_key=self.a2a_api_key)
            logger.info("TBAC SDKs initialized successfully")
        except Exception as e:
            logger.error(f"TBAC setup failed: {e}")
    
    def authorize_client_to_a2a(self):
        """Authorize client agent to communicate with A2A service"""
        if not self.client_sdk or not self.a2a_sdk:
            return True  # Skip if not configured
        
        try:
            # Get access token for client to access A2A service
            self.client_token = self.client_sdk.access_token(self.a2a_id)
            
            if not self.client_token:
                logger.error("TBAC FAILED: Could not get client agent token")
                return False
            
            # Authorize the token with A2A service
            self.client_authorized = self.a2a_sdk.authorize(self.client_token)
            
            if self.client_authorized:
                logger.info("TBAC: Client agent authorized to A2A service")
                return True
            else:
                logger.error("TBAC FAILED: Client agent not authorized by A2A service")
                return False
                
        except Exception as e:
            logger.error(f"TBAC client-to-a2a authorization failed: {e}")
            return False
    
    def authorize_a2a_to_client(self):
        """Authorize A2A service to communicate with client agent"""
        if not self.client_sdk or not self.a2a_sdk:
            return True  # Skip if not configured
        
        try:
            # Get access token for A2A service to access client
            self.a2a_token = self.a2a_sdk.access_token(self.client_id)
            
            if not self.a2a_token:
                logger.error("TBAC FAILED: Could not get A2A service token")
                return False
            
            # Authorize the token with client agent
            self.a2a_authorized = self.client_sdk.authorize(self.a2a_token)
            
            if self.a2a_authorized:
                logger.info("TBAC: A2A service authorized to client agent")
                return True
            else:
                logger.error("TBAC FAILED: A2A service not authorized by client agent")
                return False
                
        except Exception as e:
            logger.error(f"TBAC A2A-to-client authorization failed: {e}")
            return False
    
    def authorize_bidirectional(self):
        """Perform bidirectional authorization"""
        client_to_a2a = self.authorize_client_to_a2a()
        a2a_to_client = self.authorize_a2a_to_client()
        return client_to_a2a and a2a_to_client
    
    def is_client_authorized(self):
        """Check if client agent is authorized to communicate with A2A service"""
        return self.client_authorized or not all([self.client_api_key, self.a2a_api_key])
    
    def is_a2a_authorized(self):
        """Check if A2A service is authorized to communicate with client agent"""
        return self.a2a_authorized or not all([self.client_api_key, self.a2a_api_key])
    
    def is_fully_authorized(self):
        """Check if both directions are authorized"""
        return self.is_client_authorized() and self.is_a2a_authorized()
    
    def is_voice_authorized(self):
        """Check if voice agent is authorized to call A2A service"""
        return self.is_client_authorized()
    
    def check_voice_authorization(self):
        """Block if voice agent not authorized - raises exception"""
        if not self.is_voice_authorized():
            raise PermissionError("TBAC: Voice agent not authorized to communicate with A2A service")
    
    def check_a2a_authorization(self):
        """Block if A2A service not authorized - raises exception"""
        if not self.is_a2a_authorized():
            raise PermissionError("TBAC: A2A service not authorized to handle messages")