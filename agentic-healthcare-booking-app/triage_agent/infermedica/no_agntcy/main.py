"""
Main entry point for A2A Medical Triage Service
"""
import argparse
import logging
from service.triage_service import A2ATriageService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='A2A Medical Triage Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8887, help='Port to bind to (default: 8887)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        service = A2ATriageService(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        service.run()
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()