from enum import Enum

class TaskState(str, Enum):
    """A2A Task States as defined in the Agent-to-Agent protocol"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"
    UNKNOWN = "unknown"

class JSONRPCErrorCode(int, Enum):
    """JSON-RPC 2.0 Error Codes as defined in the specification"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TASK_NOT_FOUND = -32001
    TASK_CANNOT_BE_CONTINUED = -32002

class JSONRPCErrorDescription(str, Enum):
    """JSON-RPC 2.0 Error Descriptions as defined in the specification"""
    PARSE_ERROR = "Server received JSON that was not well-formed"
    INVALID_REQUEST = "The JSON payload was valid JSON, but not a valid JSON-RPC Request object"
    METHOD_NOT_FOUND = "The requested A2A RPC method does not exist or is not supported"
    INVALID_PARAMS = "The params provided for the method are invalid"
    INTERNAL_ERROR = "An unexpected error occurred on the server during processing"
    TASK_NOT_FOUND = "Task not found"
    TASK_CANNOT_BE_CONTINUED = "Task cannot be continued or canceled"