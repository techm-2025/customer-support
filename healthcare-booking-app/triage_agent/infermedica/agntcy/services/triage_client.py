import base64
import logging
import requests
from ioa_observe.sdk.decorators import tool, task
logger = logging.getLogger(__name__)

class TriageClient:

    def __init__(self, service):
        self.service = service

    def _timed_external_request(self, method, url, description, **kwargs):
        """Make a timed request to external API"""
        try:
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code != 200:
                logger.error(f"External API error: {response.status_code} - {response.text[:300]}")
            
            return response, 0
            
        except Exception as e:
            logger.error(f"External API request failed: {e}")
            raise e
        
    def _get_triage_token(self):
        """Get authentication token from external triage API with timing"""
        
        creds = base64.b64encode(f"{self.triage_app_id}:{self.triage_app_key}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}",
            "instance-id": self.triage_instance_id
        }
        payload = {"grant_type": "client_credentials"}
        
        response, elapsed = self._timed_external_request(
            'POST', self.triage_token_url, "Get OAuth Token",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            token = response.json()['access_token']
            return token
        
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
    
    @task(name="create_triage_survey", description="create a new triage survey session", version=1)
    def _create_triage_survey(self, token, age, sex):
        """Create a new triage survey with timing"""
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "sex": sex.lower(),
            "age": {"value": age, "unit": "year"}
        }
        
        response, elapsed = self._timed_external_request(
            'POST', f"{self.triage_base_url}/surveys", "Create Survey",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            survey_id = response.json()['survey_id']
            return survey_id
        
        raise Exception(f"Failed to create survey: {response.status_code} - {response.text}")
    
    def _send_triage_api_message(self, token, survey_id, message):
        """Send message to external triage API with timing"""
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"user_message": message}
        
        response, elapsed = self._timed_external_request(
            'POST', f"{self.triage_base_url}/surveys/{survey_id}/messages", 
            "Send Message",
            headers=headers, json=payload, timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            external_state = data.get('survey_state', 'in_progress')
            agent_response = data.get('assistant_message', '')
            
            
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
        
    def _get_triage_summary(self, task):
        """Get triage summary from external API with timing"""
        try:
            token = task['metadata']['triage_token']
            survey_id = task['metadata']['survey_id']
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response, elapsed = self._timed_external_request(
                'GET', f"{self.triage_base_url}/surveys/{survey_id}/summary", 
                "Get Triage Summary",
                headers=headers, timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
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