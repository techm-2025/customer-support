"""
Healthcare Voice Agent - Main Entry Point with TBAC Patching
"""
import asyncio
import os
import sys
from config.settings import Settings
from common.identity.tbac import TBAC
from common.observe.observe_config import initialize_observability


# Global TBAC instance
tbac = TBAC()


def display_startup_banner():
    """Display startup information"""
    print("=" * 60)
    print("HEALTHCARE VOICE + A2A + MCP AGENT")
    print("=" * 60)


def check_configuration():
    """Validate required environment variables"""
    settings = Settings()
    
    missing = []
    
    # Check JWT/LLM config
    if not all([settings.jwt_token, settings.endpoint_url, 
                settings.project_id, settings.connection_id]):
        missing.extend(['JWT_TOKEN', 'ENDPOINT_URL', 'PROJECT_ID', 'CONNECTION_ID'])
    
    # Check Insurance/MCP config
    if not all([settings.mcp_url, settings.insurance_api_key]):
        missing.extend(['MCP_URL', 'X_INF_API_KEY'])
    
    # Check A2A config
    if not all([settings.a2a_service_url, settings.a2a_message_url, settings.a2a_api_key]):
        missing.extend(['A2A_SERVICE_URL', 'A2A_MESSAGE_URL', 'A2A_API_KEY'])
    
    if missing:
        print(f"❌ ERROR: Missing configuration: {', '.join(set(missing))}")
        return False
    
    print("✓ Configuration validated")
    return True


def check_tbac_status():
    """Initialize and check TBAC authorization"""
    print("\n" + "=" * 60)
    print("TBAC (Task-Based Access Control) Status")
    print("=" * 60)
    
    # Display TBAC configuration
    if not all([tbac.client_api_key, tbac.client_id, tbac.a2a_api_key, tbac.a2a_id]):
        print("⚠️  TBAC: DISABLED (missing credentials)")
        print("   Agent will run without token-based authorization")
        return
    
    print("✓ TBAC: ENABLED")
    print(f"  Client Agent ID: {tbac.client_id}")
    print(f"  A2A Service ID: {tbac.a2a_id}")
    
    # Perform bidirectional authorization
    print("\nPerforming bidirectional authorization...")
    
    if tbac.authorize_bidirectional():
        print("✓ TBAC: FULLY AUTHORIZED")
        print(f"  ✓ Voice Agent → A2A Service: AUTHORIZED")
        print(f"  ✓ A2A Service → Voice Agent: AUTHORIZED")
    else:
        print("❌ TBAC: AUTHORIZATION FAILED")
        if not tbac.is_client_authorized():
            print("  ✗ Voice Agent → A2A Service: UNAUTHORIZED")
        if not tbac.is_a2a_authorized():
            print("  ✗ A2A Service → Voice Agent: UNAUTHORIZED")
        
        print("\n⚠️  WARNING: Agent will be blocked from A2A communication")


def patch_with_tbac():
    """Patch agent components with TBAC authorization checks"""
    print("\n" + "=" * 60)
    print("TBAC Patching")
    print("=" * 60)
    
    # Skip patching if TBAC not configured
    if not all([tbac.client_api_key, tbac.client_id, tbac.a2a_api_key, tbac.a2a_id]):
        print("⚠️  TBAC patching skipped (not configured)")
        return
    
    try:
        # Import modules to patch
        from clients import a2a_client
        from agent import healthcare_agent
        
        # Patch A2AClient.send_message
        if hasattr(a2a_client, 'A2AClient'):
            original_send = a2a_client.A2AClient.send_message
            
            async def patched_send(self, message_parts, task_id=None, context_id=None):
                """Patched send_message with TBAC authorization check"""
                if not tbac.is_voice_authorized():
                    print("❌ TBAC: Voice agent NOT AUTHORIZED to send message to A2A service")
                    return None
                
                print("✓ TBAC: Voice agent authorized - allowing A2A message")
                return await original_send(self, message_parts, task_id, context_id)
            
            a2a_client.A2AClient.send_message = patched_send
            print("✓ Patched: A2AClient.send_message with authorization check")
        
        # Patch HealthcareAgent._start_integrated_triage
        if hasattr(healthcare_agent, 'HealthcareAgent'):
            original_triage = healthcare_agent.HealthcareAgent._start_integrated_triage
            
            async def patched_triage(self):
                """Patched triage start with TBAC authorization check"""
                if not tbac.is_voice_authorized():
                    print("❌ TBAC: Medical triage BLOCKED - Voice agent not authorized")
                    await self.audio.speak("I apologize, but medical triage is not available at this time.")
                    self.session.add_interaction("assistant", "Medical triage unavailable due to authorization.")
                    return
                
                print("✓ TBAC: Triage authorized - proceeding")
                return await original_triage(self)
            
            healthcare_agent.HealthcareAgent._start_integrated_triage = patched_triage
            print("✓ Patched: HealthcareAgent._start_integrated_triage with authorization check")
        
        print("\n✓ TBAC patching complete - authorization checks active")
        
    except ImportError as e:
        print(f"❌ TBAC patching failed: {e}")
        print("   Agent modules not found - ensure correct import paths")
        sys.exit(1)
    except Exception as e:
        print(f"❌ TBAC patching error: {e}")
        sys.exit(1)


def display_system_info(settings):
    """Display system configuration"""
    print("\n" + "=" * 60)
    print("System Configuration")
    print("=" * 60)
    print(f"A2A Service URL: {settings.a2a_service_url}")
    print(f"A2A Message URL: {settings.a2a_message_url}")
    print(f"MCP URL: {settings.mcp_url}")
    print(f"Audio System: {'ENABLED' if settings.audio_available else 'DISABLED (console mode)'}")
    print("=" * 60 + "\n")


async def run_agent():
    """Run the healthcare agent"""
    try:
        from agent.healthcare_agent import HealthcareAgent
        agent = HealthcareAgent()
        await agent.start()
    except KeyboardInterrupt:
        print("\n\n✓ Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Agent error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    display_startup_banner()
    
    # Initialize observability
    initialize_observability("Healthcare_Voice_Agent")
    
    # Check configuration
    if not check_configuration():
        return
    
    # Check and display TBAC status
    check_tbac_status()
    
    # Patch components with TBAC authorization
    patch_with_tbac()
    
    # Display system info
    settings = Settings()
    display_system_info(settings)
    
    # Run the agent
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n✓ Shutting down gracefully...")


if __name__ == "__main__":
    main()