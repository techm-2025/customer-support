# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
Flask route definitions
"""
import logging
from datetime import datetime
from flask import request, jsonify
from a2a.types import JSONRPCErrorResponse, JSONParseError, InvalidRequestError, MethodNotFoundError, InvalidParamsError, InternalError, TaskNotFoundError, TaskNotCancelableError

logger = logging.getLogger(__name__)


def setup_routes(app, service):
    """Setup all Flask routes"""
    
    @app.route('/.well-known/agent-card.json', methods=['GET'])
    def agent_card():
        """A2A Agent Discovery Card"""
        return jsonify({
            "name": "Medical Triage Agent A2A service",
            "description": "A2A service for an AI agent that performs medical symptom triage and assessment using professional medical protocols",
            "url": f"http://{request.host}",
            "provider": {
                "organization": "Outshift",
                "url": f"http://{request.host}"
            },
            "iconUrl": f"http://{request.host}/icon.png",
            "version": "1.0.0",
            "documentationUrl": f"http://{request.host}/docs",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
                "stateTransitionHistory": False,
                "extensions": []
            },
            "securitySchemes": {
                "noAuth": {
                    "type": "http",
                    "scheme": "none"
                }
            },
            "security": [],
            "defaultInputModes": ["text/plain", "application/json"],
            "defaultOutputModes": ["text/plain", "application/json"],
            "skills": [
                {
                    "id": "medical-triage",
                    "name": "Medical Symptom Triage A2A Service",
                    "description": "Performs comprehensive medical symptom assessment and triage using AI-powered clinical protocols",
                    "tags": ["healthcare", "triage", "medical", "symptoms", "diagnosis"],
                    "examples": [
                        "I have chest pain and shortness of breath",
                        "My child has a fever and headache",
                        "I'm experiencing severe abdominal pain"
                    ],
                    "inputModes": ["text/plain", "application/json"],
                    "outputModes": ["text/plain", "application/json"]
                }
            ],
            "supportsAuthenticatedExtendedCard": False
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for load balancers"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "active_tasks": len(service.tasks)
        })
    
    @app.route('/docs', methods=['GET'])
    def documentation():
        """Basic documentation endpoint"""
        return jsonify({
            "title": "Medical Triage A2A Service",
            "description": "Agent-to-Agent protocol service for medical symptom triage",
            "endpoints": {
                "/.well-known/agent.json": "Agent discovery card",
                "/health": "Health check",
                "/docs": "This documentation",
                "/": "JSON-RPC 2.0 endpoint for A2A communication"
            },
            "supported_methods": [
                "message/send",
                "tasks/get",
                "tasks/cancel"
            ]
        })
    
    @app.route('/', methods=['POST'])
    def handle_jsonrpc():
        """Main JSON-RPC 2.0 endpoint for A2A protocol"""
        try:
            data = request.get_json()
            
            if not service.validate_jsonrpc_request(data):
                logger.warning(f"Invalid JSON-RPC request: {data}")
                return jsonify(service.create_error_response(
                    data.get('id'), InvalidRequestError, InvalidRequestError.message
                ))
            
            method = data['method']
            params = data.get('params', {})
            request_id = data['id']
            
            logger.info(f"Handling {method} request with ID {request_id}")
            
            if method == 'message/send':
                return jsonify(service.handle_message_send(params, request_id))
            elif method == 'tasks/get':
                return jsonify(service.handle_tasks_get(params, request_id))
            elif method == 'tasks/cancel':
                return jsonify(service.handle_tasks_cancel(params, request_id))
            else:
                logger.warning(f"Unknown method: {method}")
                return jsonify(service.create_error_response(
                    request_id, MethodNotFoundError, MethodNotFoundError.message
                ))
                
        except Exception as e:
            logger.error(f"Error handling JSON-RPC request: {e}", exc_info=True)
            return jsonify(service.create_error_response(
                None, InternalError, InternalError.message
            ))
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500