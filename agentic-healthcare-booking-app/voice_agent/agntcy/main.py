# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
from agent.healthcare_agent import HealthcareAgent
from audio.audio import AUDIO_AVAILABLE

from common.observe.observe_config import initialize_observability
from common.identity.tbac import TBAC
from agent.healthcare_agent import HealthcareAgent

from dotenv import load_dotenv
load_dotenv()

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
    missing.extend([var for var in jwt_required if not os.getenv(var)])
    missing.extend([var for var in insurance_required if not os.getenv(var)])
    missing.extend([var for var in a2a_required if not os.getenv(var)])
    
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
    
    # TBAC
    print("TBAC Authorization.....")
    tbac = TBAC()
    auth_success = tbac.authorize_bidirectional()
    if auth_success:
        print("TBAC Authorization successful")
    else:
        print("TBAC Authorization failed")

   # APPLY TBAC PATCHES
    print("\n--- Applying TBAC Patches ---")
    try:
        from clients import a2a_client
        from agent import healthcare_agent
        
        # Patch A2AClient.send_message
        if hasattr(a2a_client, 'A2AClient'):
            original_send = a2a_client.A2AClient.send_message
            
            async def patched_send(self, message_parts, task_id=None, context_id=None):
                if not tbac.authorize_bidirectional():
                    print("TBAC: Voice agent not authorized to send message to A2A service")
                    return None
                return await original_send(self, message_parts, task_id, context_id)
            
            a2a_client.A2AClient.send_message = patched_send
            print("✓ TBAC: Patched A2AClient.send_message")
        
        # Patch HealthcareAgent._start_integrated_triage
        if hasattr(healthcare_agent, 'HealthcareAgent'):
            original_triage = healthcare_agent.HealthcareAgent._start_integrated_triage
            
            async def patched_triage(self):
                if not tbac.authorize_bidirectional():
                    print("TBAC: Triage blocked - voice agent not authorized")
                    await self.audio.speak("Medical triage is currently unavailable. Let me help you schedule your appointment.")
                    self.session.add_interaction("assistant", "Medical triage is currently unavailable. Let me help you schedule your appointment.")
                    return {
                        "goto": "__end__",
                        "error": True,
                        "success": False,
                        "reason": "tbac_authorization_failed"
                    }
                return await original_triage(self)
            
            healthcare_agent.HealthcareAgent._start_integrated_triage = patched_triage
            print("✓ TBAC: Patched HealthcareAgent._start_integrated_triage")
        
        # Patch HealthcareAgent._handle_triage_conversation
        if hasattr(healthcare_agent, 'HealthcareAgent'):
            original_handle = healthcare_agent.HealthcareAgent._handle_triage_conversation
            
            async def patched_handle(self, user_input):
                if not tbac.authorize_bidirectional():
                    print("TBAC: Triage conversation blocked - voice agent not authorized")
                    await self._end_triage_mode("I apologize, but I need to end the medical assessment. Let me help you continue with scheduling.")
                    return {
                        "goto": "__end__",
                        "error": True,
                        "success": False,
                        "reason": "tbac_authorization_lost"
                    }
                return await original_handle(self, user_input)

            healthcare_agent.HealthcareAgent._handle_triage_conversation = patched_handle
            print("✓ TBAC: Patched HealthcareAgent._handle_triage_conversation")
        
        print("✓ TBAC: All patches applied successfully\n")
        
    except Exception as e:
        print(f"⚠ TBAC: Patching failed: {e}\n")
    
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