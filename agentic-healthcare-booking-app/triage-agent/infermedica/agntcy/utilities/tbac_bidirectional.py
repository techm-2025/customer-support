import os
import sys
from dotenv import load_dotenv
from identityservice.sdk import IdentityServiceSdk  
import importlib

load_dotenv()

from common.tbac import TBAC

# global TBAC instance
tbac = TBAC()

# import and patch
try:

    # patch A2A Client
    aac1 = importlib.import_module('voice-agent.agntcy.services.a2a_client')
    aac = aac1.A2AClient
    print("TBAC: Imported A2AClient module")

    if hasattr(aac, 'A2AClient'):
        original_send = aac.A2AClient.send_message

        async def patched_send(self, message_parts, task_id=None, context_id=None):
            if not tbac.is_voice_authorized():
                print("TBAC: Voice agent not authorized to send message to A2A")
                return None
            return await original_send(self, message_parts, task_id, context_id)
        aac.A2AClient.send_message = patched_send
        print("TBAC: Patched A2AClient.send_message with authorization check")
    
    # patch A2A service
    aas1=importlib.import_module('triage-agent.infermedica.agntcy.service.triage_service')
    aas = aas1.A2ATriageService
    print("TBAC: Imported A2AService module")

    if hasattr(aas, 'A2ATriageService'):
        original_handle = aas.A2ATriageService._handle_message_send

        def patched_handle(self, params, request_id):
            if not tbac.is_a2a_authorized():
                print("TBAC: A2A service not authorized to handle messages")
                return {"error": "A2A service blocked"}
            return original_handle(self, params, request_id)
        aas.A2ATriageService._handle_message_send = patched_handle
        print("TBAC: Patched A2ATriageService._handle_message_send with authorization check")



    # Patch voice agent
    ha1 = importlib.import_module('voice-agent.agntcy.agent.healthcare_agent')
    ha = ha1.HealthcareAgent
    print("TBAC: Imported HealthcareAgent module")

    if hasattr(ha, 'HealthcareAgent'):
        original_triage = ha.HealthcareAgent._start_integrated_triage

        async def patched_triage(self, message):
            if not tbac.is_voice_authorized():
                print("TBAC: Triage blocked")
                return {"error": "Medical Triage is not available."}
            return await original_triage(self, message)
        ha.HealthcareAgent.process_message = patched_triage
        print("TBAC: Patched VoiceAgent.process_message with authorization check")

except ImportError:
    print("TBAC: e2e_final module not found, skipping patches")
    sys.exit(1)

def run_tbac():
    print("Running with bidirectional TBAC...")

    m1= importlib.import_module('voice-agent.agntcy.main')
    m2= importlib.import_module('triage-agent.infermedica.agntcy.main')

    # authorize first
    if not tbac.authorize_bidirectional():
        print("TBAC authorization failed - running without TBAC")
        print(f"Voice authorized: {tbac.is_voice_authorized()}")
        print(f"A2A authorized: {tbac.is_a2a_authorized()}")

    # run service or agent
    if len(sys.argv) > 1 and sys.argv[1] == 'service':
            m2.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'agent':
            m1.run_agent()

if __name__ == "__main__":
    run_tbac()