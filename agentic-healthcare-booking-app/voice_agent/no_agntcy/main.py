"""
Healthcare Voice + A2A + MCP Agent
Main entry point
"""
import asyncio

from agent.healthcare_agent import HealthcareAgent
from config.settings import Settings

# Check audio availability
try:
    import speech_recognition
    import pygame
    from gtts import gTTS
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


def print_banner():
    """Print application banner"""
    print("=" * 50)
    print("HEALTHCARE VOICE + A2A + MCP AGENT")
    print("=" * 50)


def validate_configuration(settings: Settings) -> bool:
    """
    Validate all required configuration
    
    Args:
        settings: Application settings
        
    Returns:
        True if valid, False otherwise
    """
    missing = settings.validate_all()
    
    if missing:
        print(f"ERROR: Missing configuration variables:")
        for var in missing:
            print(f"  - {var}")
        return False
    
    return True


async def run_agent():
    """Main agent execution"""
    print_banner()
    
    # Load and validate settings
    settings = Settings()
    
    if not validate_configuration(settings):
        print("\nPlease check your .env file and ensure all required variables are set.")
        return
    
    print("Configuration validated")
    #settings.print_summary()
    
    # Check audio availability
    if AUDIO_AVAILABLE:
        print("\nAudio system available - Voice interaction enabled")
    else:
        print("\nAudio libraries not available - Console mode only")
        print("Install audio dependencies: pip install SpeechRecognition pyaudio pygame gtts")
    
    # Start agent
    try:
        print("\nStarting healthcare agent...")
        agent = HealthcareAgent(settings)
        await agent.start()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
    except Exception as e:
        print(f"\nAgent error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Application entry point"""
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()