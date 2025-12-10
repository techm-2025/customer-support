# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
Configuration and environment settings management
"""
import os
from dataclasses import dataclass
from typing import Optional


def load_env():
    """Load environment variables from .env file if available"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@dataclass
class LLMConfig:
    """LLM service configuration"""
    jwt_token: str
    endpoint_url: str
    project_id: str
    connection_id: str
    
    @classmethod
    def from_env(cls):
        return cls(
            jwt_token=os.getenv('JWT_TOKEN', ''),
            endpoint_url=os.getenv('ENDPOINT_URL', ''),
            project_id=os.getenv('PROJECT_ID', ''),
            connection_id=os.getenv('CONNECTION_ID', '')
        )
    
    def validate(self):
        """Validate all required fields are present"""
        missing = []
        if not self.jwt_token:
            missing.append('JWT_TOKEN')
        if not self.endpoint_url:
            missing.append('ENDPOINT_URL')
        if not self.project_id:
            missing.append('PROJECT_ID')
        if not self.connection_id:
            missing.append('CONNECTION_ID')
        return missing


@dataclass
class InsuranceConfig:
    """Insurance MCP service configuration"""
    mcp_url: str
    api_key: str
    
    @classmethod
    def from_env(cls):
        return cls(
            mcp_url=os.getenv('MCP_URL', ''),
            api_key=os.getenv('X_INF_API_KEY', '')
        )
    
    def validate(self):
        """Validate all required fields are present"""
        missing = []
        if not self.mcp_url:
            missing.append('MCP_URL')
        if not self.api_key:
            missing.append('X_INF_API_KEY')
        return missing


@dataclass
class A2AConfig:
    """A2A service configuration"""
    service_url: str
    message_url: str
    api_key: Optional[str]
    
    @classmethod
    def from_env(cls):
        base_url = os.getenv('A2A_SERVICE_URL', 'http://localhost:8887')
        return cls(
            service_url=base_url,
            message_url=os.getenv('A2A_MESSAGE_URL', base_url),
            api_key=os.getenv('A2A_API_KEY')
        )
    
    def validate(self):
        """Validate all required fields are present"""
        missing = []
        if not self.service_url:
            missing.append('A2A_SERVICE_URL')
        if not self.message_url:
            missing.append('A2A_MESSAGE_URL')
        return missing


class Settings:
    """Application settings"""
    
    def __init__(self):
        load_env()
        self.llm = LLMConfig.from_env()
        self.insurance = InsuranceConfig.from_env()
        self.a2a = A2AConfig.from_env()
    
    def validate_all(self):
        """Validate all configuration and return list of missing variables"""
        missing = []
        missing.extend(self.llm.validate())
        missing.extend(self.insurance.validate())
        missing.extend(self.a2a.validate())
        return missing
    
    def print_summary(self):
        """Print configuration summary"""
        print("Configuration Summary:")
        print(f"  LLM Endpoint: {self.llm.endpoint_url}")
        print(f"  Insurance MCP: {self.insurance.mcp_url}")
        print(f"  A2A Service: {self.a2a.service_url}")
        print(f"  A2A Message: {self.a2a.message_url}")