import os
import sys
from dotenv import load_dotenv
from identityservice.sdk import IdentityServiceSdk

load_dotenv()

class TBAC:
    def __init__(self):
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

        self._setup()

    def _setup(self):
        if not all([self.client_api_key, self.client_id, self.a2a_api_key, self.a2a_id]):
            print("TBAC Disabled: Missing credentials:")
            return

        try:
            self.client_sdk = IdentityServiceSdk(api_key=self.client_api_key)
            self.a2a_sdk = IdentityServiceSdk(api_key=self.a2a_api_key)
            print("TBAC SDKs initialized")
        except Exception as e:
            print(f"TBAC setup failed: {e}")

    def authorize_client_toa2a(self):
        """ get client agent token and authorize with A2A service """
        if not self.client_sdk or not self.a2a_sdk:
            print("TBAC bypassed")
            return True

        try:
            print("TBAC: Getting client agent access token...")
            self.client_token = self.client_sdk.access_token(agentic_service_id=self.a2a_id)

            if not self.client_token:
                print("TBAC FAILED: Could not get client agent token")
                return False

            print(f"TBAC SUCCESS: client token obtained: {self.client_token}...")

            print("TBAC: Authorizing client token with A2A service...")
            self.client_authorized = self.a2a_sdk.authorize(self.client_token)

            if self.client_authorized:
                print("TBAC SUCCESS: client agent authorized by A2A service")
                return True
            else:
                print("TBAC FAILED: client agent not authorized by A2A service")
                return False

        except Exception as e:
            print(f"TBAC process failed: {e}")
            return False

    def authorize_a2a_to_client(self):
        """A2A service gets token and authorizes with client agent"""
        if not self.client_sdk or not self.a2a_sdk:
            print("TBAC bypassed - A2A to client")
            return True

        try:
            print("TBac: A2A service getting access token..")
            self.a2a_token = self.a2a_sdk.access_token(agentic_service_id=self.client_id)

            if not self.a2a_token:
                print("TBAC FAILED: Could not get a2a service token")
                return False

            print(f"TBAC SUCCESS: a2a token obtained: {self.a2a_token}...")

            print("TBAC: Authorizing a2a token with client agent...")
            self.a2a_authorized = self.client_sdk.authorize(self.a2a_token)

            if self.a2a_authorized:
                print("TBAC SUCCESS: A2A service authorized by client agent")
                return True
            else:
                print("TBAC FAILED: A2A service not authorized by client agent")
                return False

        except Exception as e:
            print(f"TBAC A2A to client process failed: {e}")
            return False

    def authorize_bidirectional(self):
        client_to_a2a_success = self.authorize_client_toa2a()
        a2a_to_client_success = self.authorize_a2a_to_client()

        return client_to_a2a_success and a2a_to_client_success

    def is_client_authorized(self):
        # check if client agent is authorized to communicate with A2A service
        return self.client_authorized or not all([self.client_api_key, self.a2a_api_key])

    def is_a2a_authorized(self):
        # check if A2A service is authorized to communicate with client agent
        return self.a2a_authorized or not all([self.client_api_key, self.a2a_api_key])

    def is_fully_authorized(self):
        # check of both directions are authorized
        return self.is_client_authorized() and self.is_a2a_authorized()


# global TBAC instance
tbac = TBAC()