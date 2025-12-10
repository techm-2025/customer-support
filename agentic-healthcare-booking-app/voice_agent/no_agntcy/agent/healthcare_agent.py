# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
Main healthcare agent orchestration
"""
import random
import string
from typing import Optional

from audio.audio import AudioSystem
from clients.a2a_client import A2AClient
from clients.llm_client import LLMClient
from clients.insurance_client import InsuranceClient
from config.settings import Settings
from session.session import Session
from a2a.types import TaskState


class HealthcareAgent:
    """Main healthcare appointment agent with voice, triage, and insurance"""
    
    def __init__(self, settings: Settings):
        self.session = Session()
        self.audio = AudioSystem()
        
        # Initialize clients
        self.llm = LLMClient(settings.llm)
        self.insurance = InsuranceClient(settings.insurance)
        
        # Initialize A2A client
        self.a2a_client: Optional[A2AClient] = None
        try:
            self.a2a_client = A2AClient(settings.a2a)
        except Exception as e:
            print(f"A2A client initialization failed: {e}")
    
    async def start(self):
        """Start the healthcare agent conversation"""
        print(f"Healthcare Agent starting - Session {self.session.id}")
        
        # Discover A2A agent if available
        if self.a2a_client:
            await self.a2a_client.discover_agent()
        
        # Initial greeting
        initial_message = (
            "Hello! I'm your healthcare appointment assistant. "
            "Let's start by getting your basic information. "
            "What's your full name?"
        )
        await self.audio.speak(initial_message)
        self.session.add_interaction("assistant", initial_message)
        
        # Main conversation loop
        turn = 0
        errors = 0
        max_turns = 50
        max_errors = 3
        
        while turn < max_turns and errors < max_errors:
            turn += 1
            print(f"--- Turn {turn} ---")
            
            # Listen for user input
            user_input = await self.audio.listen(timeout=5)
            
            # Handle audio errors
            if user_input in ["UNCLEAR", "TIMEOUT", "ERROR"]:
                errors += 1
                if user_input == "TIMEOUT":
                    await self.audio.speak(
                        "I'm still here. What would you like me to help you with?"
                    )
                else:
                    await self.audio.speak(
                        "I didn't catch that clearly. Could you please repeat?"
                    )
                continue
            
            if not user_input:
                continue
            
            errors = 0
            print(f"USER: {user_input}")
            self.session.add_interaction("user", user_input)
            
            # Check for exit commands
            if any(phrase in user_input.lower() for phrase in ['bye', 'goodbye', 'end', 'quit']):
                await self.audio.speak("Thank you for calling. Have a great day!")
                self.session.add_interaction("assistant", "Thank you for calling. Have a great day!")
                break
            
            # Handle triage or regular conversation
            if self.session.in_triage_mode:
                await self._handle_triage_conversation(user_input)
            else:
                await self._handle_regular_conversation(user_input)
        
        # End of conversation
        print(f"Conversation ended. Final data: {self.session.data}")
        
        saved_file = self.session.save_to_file()
        if saved_file:
            print(f"Session saved to: {saved_file}")
    
    async def _handle_regular_conversation(self, user_input: str):
        """Handle regular appointment scheduling conversation"""
        # Process through LLM
        result = await self.llm.process(user_input, self.session)
        
        # Extract and update session data
        if result.get("extract"):
            self.session.update_multiple(result["extract"])
        
        # Check if triage is needed
        if (result.get("need_triage") and 
            not self.session.triage_complete and 
            self.session.triage_attempts < 1 and 
            self.a2a_client):
            
            print("TRIAGE: Starting integrated triage conversation")
            await self._start_integrated_triage()
            return
        
        # Call insurance discovery if needed
        if result.get("call_discovery"):
            await self._handle_insurance_discovery()
        
        # Call eligibility check if needed
        if result.get("call_eligibility"):
            await self._handle_eligibility_check()
        
        # Speak response
        response = result.get("response", "")
        if response:
            await self.audio.speak(response)
            self.session.add_interaction("assistant", response)
        
        # Check if done
        if result.get("done"):
            confirmation = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            final_message = (
                f"Excellent! Your appointment is confirmed. "
                f"Confirmation number: {confirmation}. "
                f"You'll receive an email confirmation shortly. "
                f"Thank you for calling!"
            )
            await self.audio.speak(final_message)
            self.session.add_interaction("assistant", final_message)
    
    async def _handle_insurance_discovery(self):
        """Call insurance discovery API"""
        required = ['name', 'date_of_birth', 'state']
        if not self.session.has_required_fields(required):
            return
        
        print("INSURANCE-DISCOVERY: Calling API...")
        discovery = await self.insurance.discovery(
            self.session.data['name'],
            self.session.data['date_of_birth'],
            self.session.data['state']
        )
        
        if discovery["success"]:
            self.session.update_data('payer', discovery['payer'])
            self.session.update_data('member_id', discovery['member_id'])
            
            message = (
                f"Great! I found your insurance: {discovery['payer']}, "
                f"Policy ID: {discovery['member_id']}."
            )
            await self.audio.speak(message)
            self.session.add_interaction("assistant", message)
        else:
            fallback_msg = "I had some trouble finding your insurance, but we can proceed."
            await self.audio.speak(fallback_msg)
            self.session.add_interaction("assistant", fallback_msg)
    
    async def _handle_eligibility_check(self):
        """Call insurance eligibility API"""
        required = ['name', 'date_of_birth', 'member_id', 'payer', 'provider_name']
        if not self.session.has_required_fields(required):
            return
        
        print("INSURANCE-ELIGIBILITY: Calling API...")
        eligibility = await self.insurance.eligibility(
            self.session.data['name'],
            self.session.data['date_of_birth'],
            self.session.data['member_id'],
            self.session.data['payer'],
            self.session.data['provider_name']
        )
        
        if eligibility["success"] and eligibility.get('copay'):
            message = (
                f"Perfect! Your insurance is verified. "
                f"Payer: {self.session.data['payer']}, "
                f"Policy ID: {self.session.data['member_id']}, "
                f"Your copay will be ${eligibility['copay']}."
            )
            await self.audio.speak(message)
            self.session.add_interaction("assistant", message)
        else:
            fallback_message = (
                f"Your insurance {self.session.data['payer']} "
                f"with Policy ID {self.session.data['member_id']} is on file. "
                f"We can proceed with scheduling."
            )
            await self.audio.speak(fallback_message)
            self.session.add_interaction("assistant", fallback_message)
    
    async def _start_integrated_triage(self):
        """Start integrated triage conversation via A2A"""
        self.session.triage_attempts += 1
        self.session.in_triage_mode = True
        
        print("TRIAGE: Starting integrated triage conversation")
        
        triage_intro = (
            "I need to do a quick medical assessment to better assist you. "
            "Let me ask you a few health-related questions."
        )
        
        try:
            await self.audio.speak(triage_intro)
            self.session.add_interaction("assistant", triage_intro)
            
            # Use default demographics for triage
            age = 33
            sex = "female"
            complaint = self.session.data.get('reason', 'general health concern')
            
            message_parts = [{
                "kind": "text",
                "text": f"I am {age} years old, {sex}. {complaint}"
            }]
            
            result = await self.a2a_client.send_message(message_parts)
            
            if not result:
                print("TRIAGE: Failed to start - falling back to normal flow")
                await self._end_triage_mode(
                    "I'll help you schedule your appointment without the assessment."
                )
                return
            
            if result.get('kind') == 'task':
                self.session.triage_task_id = result['id']
                self.session.triage_context_id = result['contextId']
                
                print(f"TRIAGE: Started task {self.session.triage_task_id}")
                
                # Speak first triage question
                if result['status'].get('message'):
                    triage_question = self._extract_text_from_message(
                        result['status']['message']
                    )
                    if triage_question:
                        await self.audio.speak(triage_question)
                        self.session.add_interaction("assistant", triage_question)
                
        except Exception as e:
            print(f"TRIAGE: Error starting: {e}")
            await self._end_triage_mode("Let me help you schedule your appointment.")
    
    async def _handle_triage_conversation(self, user_input: str):
        """Handle ongoing triage conversation"""
        print(f"TRIAGE: User response: {user_input}")
        
        try:
            message_parts = [{"kind": "text", "text": user_input}]
            result = await self.a2a_client.send_message(
                message_parts,
                task_id=self.session.triage_task_id,
                context_id=self.session.triage_context_id
            )
            
            if not result:
                print("TRIAGE: Failed to continue - ending triage")
                await self._end_triage_mode(
                    "Let me help you continue with scheduling your appointment."
                )
                return
            
            task_state = result['status']['state']
            print(f"TRIAGE: A2A task state: {task_state}")
            
            if task_state == TaskState.completed:
                print("TRIAGE: Assessment COMPLETED - exiting A2A mode")
                
                # Extract triage results
                if result.get('artifacts'):
                    artifact = result['artifacts'][0]
                    triage_data = self._extract_triage_results(artifact)
                    if triage_data:
                        self.session.triage_results.update(triage_data)
                        print(f"TRIAGE: Results extracted: {triage_data}")
                
                # Build completion message
                urgency = self.session.triage_results.get('urgency_level', 'standard')
                doctor_type = self.session.triage_results.get('doctor_type', 'general practitioner')
                
                completion_message = (
                    f"Thank you for the assessment. "
                    f"Based on your responses, I recommend seeing a {doctor_type}. "
                    f"Priority level: {urgency}. "
                    f"Now let's get you scheduled. "
                    f"I'll need your date of birth for insurance verification."
                )
                
                await self._end_triage_mode()
                await self.audio.speak(completion_message)
                self.session.add_interaction("assistant", completion_message)
                
            elif task_state == TaskState.input_required:
                # Ask next question
                if result['status'].get('message'):
                    next_question = self._extract_text_from_message(
                        result['status']['message']
                    )
                    if next_question:
                        await self.audio.speak(next_question)
                        self.session.add_interaction("assistant", next_question)
                else:
                    print("TRIAGE: No message in input-required state - ending triage")
                    await self._end_triage_mode(
                        "Let me help you continue with scheduling your appointment."
                    )
                
            elif task_state in [TaskState.failed, TaskState.canceled]:
                print(f"TRIAGE: Task ended with state: {task_state}")
                await self._end_triage_mode(
                    "Let me help you continue with scheduling your appointment."
                )
                
        except Exception as e:
            print(f"TRIAGE: Error in conversation: {e}")
            await self._end_triage_mode(
                "Let me help you continue with scheduling your appointment."
            )
    
    async def _end_triage_mode(self, message: Optional[str] = None):
        """End triage mode and return to normal flow"""
        print("TRIAGE: Ending triage mode - cleaning up A2A connection")
        
        self.session.in_triage_mode = False
        self.session.triage_complete = True
        self.session.triage_task_id = None
        self.session.triage_context_id = None
        
        print("TRIAGE: Mode ended - returning to normal appointment flow")
        
        if message:
            await self.audio.speak(message)
            self.session.add_interaction("assistant", message)
    
    def _extract_text_from_message(self, message: dict) -> Optional[str]:
        """Extract text content from A2A message"""
        if not message or not message.get('parts'):
            return None
        
        for part in message['parts']:
            if part.get('kind') == 'text':
                return part.get('text', '')
        
        return None
    
    def _extract_triage_results(self, artifact: dict) -> dict:
        """Extract triage results from artifact"""
        if not artifact or not artifact.get('parts'):
            return {}
        
        for part in artifact['parts']:
            if part.get('kind') == 'data' and part.get('data'):
                return part['data']
        
        return {}