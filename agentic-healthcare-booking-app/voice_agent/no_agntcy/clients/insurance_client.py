"""
Insurance MCP client for discovery and eligibility checks
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

import requests

from config.settings import InsuranceConfig
from utils.helpers import (
    split_name,
    format_date_of_birth,
    format_state,
    clean_provider_name,
    extract_payer,
    extract_member_id,
    extract_copay
)


class InsuranceClient:
    """Client for insurance MCP service interactions"""
    
    def __init__(self, config: InsuranceConfig):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "X-INF-API-KEY": config.api_key
        }
        print("INSURANCE: Client initialized")
    
    async def discovery(self, name: str, dob: str, state: str) -> Dict[str, Any]:
        """
        Perform insurance discovery
        
        Args:
            name: Patient full name
            dob: Date of birth
            state: US state
            
        Returns:
            Dictionary with success status, payer, and member_id
        """
        print(f"INSURANCE: Discovery - {name}, {dob}, {state}")
        
        first, last = split_name(name)
        formatted_dob = format_date_of_birth(dob)
        formatted_state = format_state(state)
        
        payload = {
            "jsonrpc": "2.0",
            "id": f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "method": "tools/call",
            "params": {
                "name": "insurance_discovery",
                "arguments": {
                    "patientDateOfBirth": formatted_dob,
                    "patientFirstName": first,
                    "patientLastName": last,
                    "patientState": formatted_state
                }
            }
        }
        
        def _request():
            return requests.post(
                self.config.mcp_url,
                headers=self.headers,
                json=payload,
                timeout=45
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _request)
        
        if response.status_code == 200:
            data = response.json()
            
            if "result" in data:
                result_text = str(data["result"])
                
                payer = extract_payer(result_text)
                member_id = extract_member_id(result_text)
                
                return {
                    "success": True,
                    "payer": payer,
                    "member_id": member_id
                }
        
        return {"success": False}
    
    async def eligibility(
        self,
        name: str,
        dob: str,
        subscriber_id: str,
        payer_name: str,
        provider_name: str
    ) -> Dict[str, Any]:
        """
        Check insurance eligibility
        
        Args:
            name: Patient full name
            dob: Date of birth
            subscriber_id: Insurance member ID
            payer_name: Insurance payer name
            provider_name: Healthcare provider name
            
        Returns:
            Dictionary with success status and copay
        """
        print(f"INSURANCE: Eligibility check")
        
        first, last = split_name(name)
        formatted_dob = format_date_of_birth(dob)
        
        provider_clean = clean_provider_name(provider_name)
        provider_first, provider_last = split_name(provider_clean)
        
        payload = {
            "jsonrpc": "2.0",
            "id": f"eligibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "method": "tools/call",
            "params": {
                "name": "benefits_eligibility",
                "arguments": {
                    "patientFirstName": first,
                    "patientLastName": last,
                    "patientDateOfBirth": formatted_dob,
                    "subscriberId": subscriber_id,
                    "payerName": payer_name,
                    "providerFirstName": provider_first,
                    "providerLastName": provider_last,
                    "providerNpi": "1234567890"
                }
            }
        }
        
        def _request():
            return requests.post(
                self.config.mcp_url,
                headers=self.headers,
                json=payload,
                timeout=45
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _request)
        
        if response.status_code == 200:
            data = response.json()
            
            if "result" in data:
                result_text = str(data["result"])
                copay = extract_copay(result_text)
                
                return {
                    "success": True,
                    "copay": copay
                }
        
        return {"success": False}