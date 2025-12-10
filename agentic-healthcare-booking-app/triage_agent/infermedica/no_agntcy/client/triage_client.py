# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
External triage API client with timing
"""
import base64
import time
import logging
import requests

logger = logging.getLogger(__name__)


class TriageAPIClient:
    """Handles all external triage API communication"""
    
    def __init__(self, config):
        self.triage_app_id = config['triage_app_id']
        self.triage_app_key = config['triage_app_key']
        self.triage_instance_id = config['triage_instance_id']
        self.triage_token_url = config['triage_token_url']
        self.triage_base_url = config['triage_base_url']
    
    def timed_external_request(self, method, url, description, **kwargs):
        """Make a timed request to external API with detailed logging"""
        start_time = time.time()
        timestamp = time.strftime("%H:%M:%S", time.localtime(start_time))
        logger.info(f"A2A-SERVICE: [{timestamp}] >>> {method} {description}")
        logger.info(f"A2A-SERVICE: URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            elapsed = time.time() - start_time
            end_timestamp = time.strftime("%H:%M:%S", time.localtime())
            elapsed_ms = elapsed * 1000
            
            logger.info(f"A2A-SERVICE: [{end_timestamp}] <<< {response.status_code} | {elapsed:.3f}s ({elapsed_ms:.0f}ms)")
            
            if response.status_code != 200:
                logger.error(f"A2A-SERVICE: Error response: {response.text[:300]}")
            else:
                logger.info(f"A2A-SERVICE: Success - response length: {len(response.text)} chars")
            
            return response, elapsed
            
        except Exception as e:
            elapsed = time.time() - start_time
            end_timestamp = time.strftime("%H:%M:%S", time.localtime())
            elapsed_ms = elapsed * 1000
            logger.error(f"A2A-SERVICE: [{end_timestamp}] <<< ERROR: {e} | {elapsed:.3f}s ({elapsed_ms:.0f}ms)")
            raise e
    
    def get_triage_token(self):
        """Get authentication token from external triage API with timing"""
        logger.info("Requesting triage API authentication token")
        
        creds = base64.b64encode(f"{self.triage_app_id}:{self.triage_app_key}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}",
            "instance-id": self.triage_instance_id
        }
        payload = {"grant_type": "client_credentials"}
        
        response, elapsed = self.timed_external_request(
            'POST', self.triage_token_url, "Get OAuth Token",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            token = response.json()['access_token']
            logger.info(f"Successfully obtained triage API token")
            return token
        
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
    
    def create_triage_survey(self, token, age, sex):
        """Create a new triage survey with timing"""
        logger.info(f"Creating triage survey - age={age}, sex={sex}")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "sex": sex.lower(),
            "age": {"value": age, "unit": "year"}
        }
        
        response, elapsed = self.timed_external_request(
            'POST', f"{self.triage_base_url}/surveys", "Create Survey",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            survey_id = response.json()['survey_id']
            logger.info(f"Successfully created triage survey: {survey_id}")
            return survey_id
        
        raise Exception(f"Failed to create survey: {response.status_code} - {response.text}")
    
    def send_triage_api_message(self, token, survey_id, message):
        """Send message to external triage API with timing"""
        logger.info(f"Sending message to triage API: '{message[:50]}...'")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"user_message": message}
        
        response, elapsed = self.timed_external_request(
            'POST', f"{self.triage_base_url}/surveys/{survey_id}/messages",
            "Send Message",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            external_state = data.get('survey_state', 'in_progress')
            agent_response = data.get('assistant_message', '')
            
            logger.info(f"Triage state: {external_state}")
            logger.info(f"Triage response length: {len(agent_response)} chars")
            
            return {
                "success": True,
                "response": agent_response,
                "state": external_state
            }
        else:
            logger.error(f"Triage API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "response": "I'm having trouble with the medical assessment system."
            }
    
    def get_triage_summary(self, token, survey_id):
        """Get triage summary from external API with timing"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response, elapsed = self.timed_external_request(
                'GET', f"{self.triage_base_url}/surveys/{survey_id}/summary",
                "Get Triage Summary",
                headers=headers, timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Triage summary retrieved successfully")
                return {
                    'success': True,
                    'urgency_level': data.get('urgency', 'standard'),
                    'doctor_type': data.get('doctor_type', 'general practitioner'),
                    'notes': data.get('notes', 'Assessment completed')
                }
            else:
                logger.warning(f"Failed to get triage summary: {response.status_code}")
                return {'success': False}
        except Exception as e:
            logger.error(f"Error getting triage summary: {e}", exc_info=True)
            return {'success': False}