"""
A2A client for hosted A2A service communication
"""
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional

import requests

from config.settings import A2AConfig


class A2AClient:
    """Client for A2A protocol communication with hosted service"""
    
    def __init__(self, config: A2AConfig):
        self.config = config
        self.agent_id = f"client_{uuid.uuid4().hex[:8]}"
        self.agent_card: Optional[Dict] = None
        
        print(f"A2A-CLIENT: Initialized as {self.agent_id}")
        print(f"A2A-CLIENT: Discovery URL: {config.service_url}")
        print(f"A2A-CLIENT: Message URL: {config.message_url}")
        print(f"A2A-CLIENT: API Key: {'Set' if config.api_key else 'Not set'}")
    
    def _timed_request(
        self,
        method: str,
        url: str,
        description: str,
        **kwargs
    ) -> tuple:
        """Execute HTTP request with timing"""
        start_time = time.time()
        timestamp = time.strftime("%H:%M:%S", time.localtime(start_time))
        print(f"A2A-CLIENT: [{timestamp}] >>> {method} {description}")
        print(f"A2A-CLIENT: URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, **kwargs)
            else:
                response = requests.post(url, **kwargs)
            
            elapsed = time.time() - start_time
            end_timestamp = time.strftime("%H:%M:%S", time.localtime())
            elapsed_ms = elapsed * 1000
            print(f"A2A-CLIENT: [{end_timestamp}] <<< {response.status_code} | {elapsed:.3f}s ({elapsed_ms:.0f}ms)")
            
            if response.status_code != 200:
                print(f"A2A-CLIENT: Error response: {response.text[:200]}")
            else:
                print(f"A2A-CLIENT: Success - response length: {len(response.text)} chars")
            
            return response, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            end_timestamp = time.strftime("%H:%M:%S", time.localtime())
            elapsed_ms = elapsed * 1000
            print(f"A2A-CLIENT: [{end_timestamp}] <<< ERROR: {e} | {elapsed:.3f}s ({elapsed_ms:.0f}ms)")
            return None, elapsed
    
    async def discover_agent(self) -> bool:
        """
        Discover agent capabilities via agent card
        
        Returns:
            True if discovery successful, False otherwise
        """
        try:
            def _request():
                return self._timed_request(
                    'GET',
                    f"{self.config.service_url}/.well-known/agent-card.json",
                    "Agent Discovery",
                    timeout=30
                )
            
            loop = asyncio.get_event_loop()
            response, elapsed = await loop.run_in_executor(None, _request)
            
            if response and response.status_code == 200:
                self.agent_card = response.json()
                print(f"A2A-CLIENT: Discovered agent: {self.agent_card['name']}")
                return True
            else:
                if response:
                    print(f"A2A-CLIENT: Discovery failed: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"A2A-CLIENT: Discovery error: {e}")
            return False
    
    async def send_message(
        self,
        message_parts: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        context_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to A2A service
        
        Args:
            message_parts: List of message parts (text, data, etc.)
            task_id: Optional task ID for continuing conversation
            context_id: Optional context ID
            
        Returns:
            Task result dictionary or None on failure
        """
        message = {
            "role": "user",
            "parts": message_parts,
            "messageId": str(uuid.uuid4()),
            "kind": "message"
        }
        
        if task_id:
            message["taskId"] = task_id
        if context_id:
            message["contextId"] = context_id
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": message,
                "configuration": {
                    "acceptedOutputModes": ["text/plain", "application/json"],
                    "blocking": True
                }
            }
        }
        
        # Log the message being sent
        message_text = self._extract_text_from_parts(message_parts)
        print(f"A2A-CLIENT: Sending message: '{message_text[:100]}...'")
        
        try:
            def _request():
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers['X-Shared-Key'] = self.config.api_key
                
                description = f"Send Message"
                if task_id:
                    description += f" (Task: {task_id})"
                
                return self._timed_request(
                    'POST',
                    self.config.message_url,
                    description,
                    json=payload,
                    headers=headers,
                    timeout=60
                )
            
            loop = asyncio.get_event_loop()
            response, elapsed = await loop.run_in_executor(None, _request)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    result = data['result']
                    state = result['status']['state']
                    task_id = result.get('id', task_id)
                    
                    print(f"A2A-CLIENT: Task {task_id} state: {state}")
                    
                    # Log agent response if present
                    if result['status'].get('message'):
                        agent_response = self._extract_text_from_message(
                            result['status']['message']
                        )
                        if agent_response:
                            print(f"A2A-CLIENT: Agent response: '{agent_response[:100]}...'")
                    
                    # Log artifacts if present
                    if result.get('artifacts'):
                        print(f"A2A-CLIENT: Task completed with {len(result['artifacts'])} artifact(s)")
                    
                    return result
                elif 'error' in data:
                    print(f"A2A-CLIENT: Server error: {data['error']}")
                    return None
            else:
                if response:
                    print(f"A2A-CLIENT: HTTP error {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"A2A-CLIENT: Request failed: {e}")
            return None
    
    def _extract_text_from_parts(self, parts: List[Dict]) -> str:
        """Extract text content from message parts"""
        for part in parts:
            if part.get('kind') == 'text':
                return part.get('text', '')
        return ""
    
    def _extract_text_from_message(self, message: Dict) -> str:
        """Extract text content from message object"""
        if not message or not message.get('parts'):
            return ""
        return self._extract_text_from_parts(message['parts'])