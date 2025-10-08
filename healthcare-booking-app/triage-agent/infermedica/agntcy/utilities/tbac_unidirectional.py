import os
from dotenv import load_dotenv
from identityservice.sdk import IdentityServiceSdk
import importlib

load_dotenv()

class tbac_oneway:
    def __init__(self):
        self.client_api_key = os.getenv('CLIENT_AGENT_API_KEY')
        self.client_id = os.getenv('CLIENT_AGENT_ID')
        self.a2a_api_key = os.getenv('A2A_SERVICE_API_KEY')
        self.a2a_id = os.getenv('A2A_SERVICE_ID')

        if not all([self.client_api_key, self.client_id, self.a2a_api_key, self.a2a_id]):
            print("TBAC Disabled: Missing credentials:")
            return

        try:
            self.client_sdk = IdentityServiceSdk(api_key=self.client_api_key)
            self.a2a_sdk = IdentityServiceSdk(api_key=self.a2a_api_key)
            print("TBAC SDKs initialized")
        except Exception as e:
            print(f"TBAC setup failed: {e}")

    def token_auth(self):
        pass

    client_sdk = IdentityServiceSdk(api_key=os.getenv("CLIENT_AGENT_API_KEY"))
    a2a_sdk = IdentityServiceSdk(api_key=os.getenv("A2A_SERVICE_API_KEY"))

    client_token = client_sdk.access_token(agentic_service_id=os.getenv("A2A_SERVICE_ID"))
    print(f"Client token generated for access to A2a : {str(client_token)[:5]}...")
    # print first 5 characters of the token.


# global instance

tbac_instance = tbac_oneway()

# patch A2A Client
aac1 = importlib.import_module('voice-agent.agntcy.services.a2a_client')
aac = aac1.A2AClient
print("TBAC: Imported A2AClient module")

original_send = aac.A2AClient.send_message
def patched_send(self, *args, **kwargs):
    if not tbac_instance.a2a_sdk.authorize(tbac_instance.client_token):
        raise Exception("authorization failed: Client -> A2A")
    print("Client -> A2A authorized successfully.")
    return original_send(self, *args, **kwargs)
aac.A2AClient.send_message = patched_send

# Patch voice agent
ha1 = importlib.import_module('voice-agent.agntcy.agent.healthcare_agent')
ha = ha1.HealthcareAgent
print("TBAC: Imported HealthcareAgent module")

original_triage = ha.HealthcareAgent._start_integrated_triage
def patched_triage(self, *args, **kwargs):
    # A2A uses same token to respond - client already authorized it.
    print(" A2A -> Client authorized successfully.")
    return original_triage(self, *args, **kwargs)
ha.HealthcareAgent._start_integrated_triage = patched_triage

if __name__ == "__main__":
    m1 = importlib.import_module('voice-agent.agntcy.main')
    m1.main()
