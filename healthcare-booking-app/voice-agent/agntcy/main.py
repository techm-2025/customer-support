import asyncio
import os
from config.settings import load_env
from agent.healthcare_agent import HealthcareAgent
from config.observe_config import initialize_observability
from services.audio_service import AUDIO_AVAILABLE

load_env()

def get_missing_env_vars(required_vars):
    """
    Generator function to yield missing environment variables from a given list.
    """
    for var in required_vars:
        if not os.getenv(var):
            yield var

def run_agent():
    print("=" * 50)
    print("HEALTHCARE VOICE + A2A + MCP AGENT")
    print("=" * 50)

    service_name = "Healthcare_Voice_Agent"
    initialize_observability(service_name)
    
    jwt_required = ['JWT_TOKEN', 'ENDPOINT_URL', 'PROJECT_ID', 'CONNECTION_ID']
    insurance_required = ['MCP_URL', 'X_INF_API_KEY']
    a2a_required = ['A2A_SERVICE_URL', 'A2A_MESSAGE_URL', 'A2A_API_KEY']
    
    missing = []
    missing.extend(get_missing_env_vars(jwt_required))
    missing.extend(get_missing_env_vars(insurance_required))
    missing.extend(get_missing_env_vars(a2a_required))
    
    if missing:
        print(f"ERROR: Missing config: {missing}")
        return
    
    print("Configuration validated")
    print(f"A2A Service URL: {os.getenv('A2A_SERVICE_URL')}")
    print(f"A2A Message URL: {os.getenv('A2A_MESSAGE_URL')}")
    
    if AUDIO_AVAILABLE:
        print("Audio system available - Triage conversation integrated")
    else:
        print("Console mode only")
    
    async def start():
        try:
            agent = HealthcareAgent()
            await agent.start()
        except KeyboardInterrupt:
            print("\nAgent stopped by user")
        except Exception as e:
            print(f"Agent error: {e}")
    
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\nShutting down...")

def main():
    run_agent()

if __name__ == "__main__":
    main()