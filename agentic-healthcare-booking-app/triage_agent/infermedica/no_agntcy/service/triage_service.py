# Copyright AGNTCY Contributors (https://github.com/agntcy)
#
# SPDX-License-Identifier: Apache-2.0

"""
Main A2A Triage Service class
"""
import logging
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from config.settings import load_env, get_triage_config

from a2a.types import TaskState, JSONRPCErrorResponse, JSONParseError, InvalidRequestError, MethodNotFoundError, InvalidParamsError, InternalError, TaskNotFoundError, TaskNotCancelableError
from client.triage_client import TriageAPIClient
from utils.task_handlers import create_new_task, continue_existing_task
from service.routes import setup_routes

logger = logging.getLogger(__name__)


class A2ATriageService:
    """
    Standalone A2A Medical Triage Service with Timing Logs
    
    Provides medical symptom triage through the Agent-to-Agent protocol,
    integrating with external medical triage APIs.
    """
    
    def __init__(self, host='0.0.0.0', port=8887, debug=False):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        self.host = host
        self.port = port
        self.debug = debug
        
        # In-memory storage for tasks and contexts
        self.tasks = {}
        self.contexts = {}
        
        # Load triage API configuration
        load_env()
        triage_config = get_triage_config()
        self.triage_client = TriageAPIClient(triage_config)
        
        # Setup Flask routes
        setup_routes(self.app, self)
        
        logger.info(f"A2A Triage Service initialized - will run on {host}:{port}")
    
    def validate_jsonrpc_request(self, data):
        """Validate JSON-RPC 2.0 request format"""
        if not isinstance(data, dict):
            return False
        if data.get('jsonrpc') != '2.0':
            return False
        if 'method' not in data:
            return False
        if 'id' not in data:
            return False
        return True
    
    def create_error_response(self, request_id, code, message, data=None):
        """Create JSON-RPC 2.0 error response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        if data:
            response["error"]["data"] = data
        return response
    
    def create_success_response(self, request_id, result):
        """Create JSON-RPC 2.0 success response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def handle_message_send(self, params, request_id):
        """Handle message/send JSON-RPC method"""
        try:
            message = params.get('message')
            if not message:
                return self.create_error_response(
                    request_id, InvalidParamsError, InvalidParamsError.message
                )
            
            parts = message.get('parts', [])
            task_id = message.get('taskId')
            context_id = message.get('contextId')
            message_id = message.get('messageId')
            
            # Extract text from message parts
            user_text = ""
            for part in parts:
                if part.get('kind') == 'text':
                    user_text = part.get('text', '')
                    break
            
            logger.info(f"Processing message: '{user_text[:100]}...'")
            
            if task_id and task_id in self.tasks:
                task = continue_existing_task(
                    self.triage_client, self.tasks, task_id, user_text, request_id, message
                )
                if task is None:
                    return self.create_error_response(request_id, TaskNotCancelableError, TaskNotCancelableError.message)
                return self.create_success_response(request_id, task)
            else:
                task = create_new_task(
                    self.triage_client, user_text, context_id, request_id, message
                )
                self.tasks[task['id']] = task
                return self.create_success_response(request_id, task)
                
        except Exception as e:
            logger.error(f"Error in message/send: {e}", exc_info=True)
            return self.create_error_response(request_id, InternalError, InternalError.message)
    
    def handle_tasks_get(self, params, request_id):
        """Handle tasks/get JSON-RPC method"""
        task_id = params.get('id')
        if not task_id or task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return self.create_error_response(request_id, TaskNotFoundError, TaskNotFoundError.message )
        
        task = self.tasks[task_id]
        history_length = params.get('historyLength', 10)
        
        # Limit history if requested
        if history_length and len(task.get('history', [])) > history_length:
            task_copy = task.copy()
            task_copy['history'] = task['history'][-history_length:]
            return self.create_success_response(request_id, task_copy)
        
        logger.info(f"Retrieved task {task_id}")
        return self.create_success_response(request_id, task)
    
    def handle_tasks_cancel(self, params, request_id):
        """Handle tasks/cancel JSON-RPC method"""
        task_id = params.get('id')
        if not task_id or task_id not in self.tasks:
            logger.warning(f"Task not found for cancellation: {task_id}")
            return self.create_error_response(request_id, TaskNotFoundError, TaskNotFoundError.message)
        
        task = self.tasks[task_id]
        
        # Check if task can be cancelled
        if task['status']['state'] in [TaskState.completed, TaskState.failed, TaskState.canceled]:
            logger.warning(f"Task {task_id} cannot be cancelled - in terminal state")
            return self.create_error_response(request_id, TaskNotCancelableError, TaskNotCancelableError.message)
        
        # Cancel the task
        task['status']['state'] = TaskState.canceled
        task['status']['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} cancelled")
        return self.create_success_response(request_id, task)
    
    def run(self):
        """Run the Flask application"""
        logger.info(f"Starting A2A Triage Service on {self.host}:{self.port}")
        logger.info(f"Agent card available at: http://{self.host}:{self.port}/.well-known/agent-card.json")
        logger.info(f"Health check available at: http://{self.host}:{self.port}/health")
        
        # Run Flask app
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False
        )