"""
Task creation and continuation handlers
"""
import re
import uuid
import logging
from datetime import datetime
from a2a.types import TaskState

logger = logging.getLogger(__name__)


def extract_demographics(text):
    """Extract age and sex from user input text"""
    demographics = {}
    
    # Age extraction patterns
    age_patterns = [
        r'\b(\d{1,2})\s*(?:years?\s*old|yo)\b',
        r'\bage\s*(?:is\s*)?(\d{1,2})\b',
        r'\bi\s*am\s*(\d{1,2})\b'
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text.lower())
        if match:
            age = int(match.group(1))
            if 1 <= age <= 120:
                demographics['age'] = age
                break
    
    # Sex extraction
    text_lower = text.lower()
    if any(word in text_lower for word in ['male', 'man', 'boy', 'he', 'his', 'him']):
        demographics['sex'] = 'male'
    elif any(word in text_lower for word in ['female', 'woman', 'girl', 'she', 'her']):
        demographics['sex'] = 'female'
    
    logger.info(f"Extracted demographics: {demographics}")
    return demographics


def start_triage_session(triage_client, age, sex, complaint, task):
    """Start a new triage session with external API"""
    try:
        token = triage_client.get_triage_token()
        survey_id = triage_client.create_triage_survey(token, age, sex)
        
        initial_response = triage_client.send_triage_api_message(token, survey_id, complaint)
        
        return {
            'success': True,
            'response': initial_response.get('response', 'Medical triage session started. Please describe your symptoms.'),
            'metadata': {
                'triage_token': token,
                'survey_id': survey_id
            }
        }
    except Exception as e:
        logger.error(f"Error starting triage session: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def create_new_task(triage_client, user_text, context_id, request_id, original_message):
    """Create a new triage task"""
    task_id = str(uuid.uuid4())
    if not context_id:
        context_id = str(uuid.uuid4())
    
    logger.info(f"Creating new triage task {task_id}")
    
    # Create task structure
    task = {
        "id": task_id,
        "contextId": context_id,
        "status": {
            "state": TaskState.submitted,
            "timestamp": datetime.now().isoformat()
        },
        "history": [original_message],
        "artifacts": [],
        "metadata": {
            "triage_token": None,
            "survey_id": None,
            "triage_state": "starting"
        },
        "kind": "task"
    }
    
    # Extract demographics from user input
    demographics = extract_demographics(user_text)
    age = demographics.get('age', 64)
    sex = demographics.get('sex', 'female')
    
    logger.info(f"Starting triage session with age={age}, sex={sex}")
    
    # Start external triage session
    result = start_triage_session(triage_client, age, sex, user_text, task)
    
    if result['success']:
        task['metadata'].update(result['metadata'])
        task['status']['state'] = TaskState.input_required
        
        # Create agent response message
        agent_message = {
            "role": "agent",
            "parts": [{"kind": "text", "text": result['response']}],
            "messageId": str(uuid.uuid4()),
            "taskId": task_id,
            "contextId": context_id,
            "kind": "message"
        }
        task['history'].append(agent_message)
        task['status']['message'] = agent_message
        task['metadata']['triage_state'] = 'in_progress'
        
        logger.info(f"Triage task {task_id} started successfully")
    else:
        task['status']['state'] = TaskState.failed
        logger.error(f"Failed to start triage for task {task_id}: {result.get('error')}")
    
    return task


def continue_existing_task(triage_client, tasks, task_id, user_text, request_id, message):
    """Continue an existing triage task"""
    task = tasks[task_id]
    
    logger.info(f"Continuing task {task_id}, current state: {task['status']['state']}")
    
    # Check if task is in a terminal state
    if task['status']['state'] in [TaskState.completed, TaskState.failed, TaskState.canceled]:
        logger.warning(f"Task {task_id} is in terminal state: {task['status']['state']}")
        return None
    
    task['history'].append(message)
    
    # Send message to external triage API
    result = triage_client.send_triage_api_message(
        task['metadata']['triage_token'],
        task['metadata']['survey_id'],
        user_text
    )
    
    if result['success']:
        # Create agent response
        agent_message = {
            "role": "agent",
            "parts": [{"kind": "text", "text": result['response']}],
            "messageId": str(uuid.uuid4()),
            "taskId": task_id,
            "contextId": task['contextId'],
            "kind": "message"
        }
        task['history'].append(agent_message)
        task['status']['message'] = agent_message
        
        # Map external triage state to A2A task state
        external_state = result.get('state', 'in_progress')
        task['metadata']['triage_state'] = external_state
        
        logger.info(f"External triage state: {external_state}")
        
        if external_state == 'present_result':
            logger.info("Triage completed - transitioning to COMPLETED state")
            task['status']['state'] = TaskState.completed
            
            # Get triage summary and create artifact
            summary_result = triage_client.get_triage_summary(
                task['metadata']['triage_token'],
                task['metadata']['survey_id']
            )
            artifact_data = {
                "urgency_level": summary_result.get('urgency_level', 'standard'),
                "doctor_type": summary_result.get('doctor_type', 'general practitioner'),
                "notes": summary_result.get('notes', 'Triage assessment completed'),
                "completed_at": datetime.now().isoformat()
            }
            
            artifact = {
                "artifactId": str(uuid.uuid4()),
                "name": "Medical Triage Assessment",
                "description": "Results from medical triage evaluation",
                "parts": [
                    {
                        "kind": "data",
                        "data": artifact_data
                    }
                ]
            }
            task['artifacts'] = [artifact]
            
            logger.info(f"Task {task_id} completed with triage results")
            
        elif external_state == 'in_progress':
            task['status']['state'] = TaskState.input_required
            logger.info(f"Task {task_id} waiting for more user input")
            
        elif external_state == 'post_result':
            logger.warning("Received post_result state - task should already be completed")
            task['status']['state'] = TaskState.completed
            
        else:
            task['status']['state'] = TaskState.input_required
            
    else:
        task['status']['state'] = TaskState.failed
        logger.error(f"Failed to process triage message for task {task_id}: {result.get('error')}")
    
    return task