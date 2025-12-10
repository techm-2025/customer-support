# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
LLM client for conversation processing
"""
import asyncio
import json
from typing import Dict, Any

import requests

from config.settings import LLMConfig


class LLMClient:
    """Client for LLM API interactions"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.jwt_token}'
        }
        print("LLM: Initialized with JWT endpoint")
    
    def _build_prompt(self, user_input: str, session) -> str:
        """Build appropriate prompt based on session state"""
        if session.in_triage_mode:
            return self._build_triage_prompt(user_input, session)
        else:
            return self._build_appointment_prompt(user_input, session)
    
    def _build_triage_prompt(self, user_input: str, session) -> str:
        """Build prompt for triage mode"""
        return f"""You are in TRIAGE MODE. The user is answering medical assessment questions.

Current triage task: {session.triage_task_id}
User response to triage question: "{user_input}"

Respond with:
{{
    "response": "I understand your answer. Let me continue the medical assessment.",
    "extract": {{}},
    "need_triage": false,
    "call_discovery": false,
    "call_eligibility": false,
    "done": false,
    "continue_triage": true
}}"""
    
    def _build_appointment_prompt(self, user_input: str, session) -> str:
        """Build prompt for appointment scheduling"""
        return f"""You are a healthcare appointment scheduler with this specific flow:

1. Ask name, phone
2. Ask reason for visit
3. If medical symptoms → start triage (use default demographics)
4. After triage → collect DOB (for insurance), state → call discovery → announce insurance found
5. Collect provider → call eligibility → announce payer, policy ID, copay
6. Schedule appointment → confirmation code → end

Current session data: {json.dumps(session.data)}
Triage complete: {session.triage_complete}
Triage results: {json.dumps(session.triage_results)}
User input: "{user_input}"

EXTRACTION RULES:
- Extract name as "name"
- Extract phone as "phone" 
- Extract medical reason as "reason"
- Extract date of birth as "date_of_birth" (MM/DD/YYYY format)
- Extract US state as "state"
- Extract provider name as "provider_name"
- Extract appointment date as "preferred_date"

JSON response:
{{
    "response": "what to say to user",
    "extract": {{"field": "value"}},
    "need_triage": true/false,
    "call_discovery": true/false,
    "call_eligibility": true/false,
    "done": true/false
}}"""
    
    async def process(self, user_input: str, session) -> Dict[str, Any]:
        """
        Process user input through LLM
        
        Args:
            user_input: User's message
            session: Current session object
            
        Returns:
            Parsed LLM response as dictionary
        """
        print(f"LLM: Processing: '{user_input[:50]}...'")
        
        prompt = self._build_prompt(user_input, session)
        
        payload = {
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            "project_id": self.config.project_id,
            "connection_id": self.config.connection_id,
            "max_tokens": 400,
            "temperature": 0.2
        }
        
        def _request():
            return requests.post(
                self.config.endpoint_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _request)
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and data['choices']:
                content = data['choices'][0]['message']['content']
                
                try:
                    # Clean JSON formatting
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    
                    result = json.loads(content.strip())
                    print("LLM: Response parsed")
                    return result
                except Exception as e:
                    print(f"LLM: Parse error: {e}")
        
        # Fallback response
        return {
            "response": "I understand. Please continue.",
            "extract": {},
            "need_triage": False,
            "call_discovery": False,
            "call_eligibility": False,
            "done": False
        }