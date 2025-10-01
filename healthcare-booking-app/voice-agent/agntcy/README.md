# Healthcare Voice + A2A + MCP Agent - Observability README

This document outlines the observability implementation for the Healthcare Voice + A2A + MCP Agent, focusing on how the `ioa_observe.sdk` is used to instrument and monitor the agent's operations, including interactions with A2A and MCP services.

## Table of Contents
1.  [Introduction](#1-introduction)
2.  [Observability Setup](#2-observability-setup)
3.  [Agent, Workflow, Task, and Tool Instrumentation](#3-agent-workflow-task-and-tool-instrumentation)
    *   [`@agent` Decorator](#agent-decorator)
    *   [`@workflow` Decorator](#workflow-decorator)
    *   [`@task` Decorator](#task-decorator)
    *   [`@tool` Decorator](#tool-decorator)
4.  [A2A Protocol Observability](#4-a2a-protocol-observability)
5.  [Metrics](#5-metrics)
6.  [Session Tracing](#6-session-tracing)

---

## 1. Introduction

The Healthcare Voice + A2A + MCP Agent is designed to automate healthcare appointment scheduling, integrating with external services for medical assessment (via A2A) and insurance verification (via MCP). To ensure robust monitoring, debugging, and performance analysis, the agent leverages the `ioa_observe.sdk` for comprehensive observability. This includes tracing, metrics, and structured logging across its various components and external interactions.

## 2. Observability Setup

The core observability initialization happens in the `run_agent` function and within the `A2AClient` constructor:

*   **Global Initialization**:
    ```python
    from triage_agent.infermedica.agntcy.observe_config.observe_config import initialize_observability
    # ...
    def run_agent():
        # ...
        service_name = "Healthcare_Voice_Agent"
        initialize_observability(service_name)
    ```
    This call sets up the foundational observability configuration for the entire agent, typically configuring OpenTelemetry exporters and resource attributes.

*   **A2A Client Specific Initialization**:
    ```python
    from ioa_observe.sdk import Observe
    from ioa_observe.sdk.instrumentations.a2a import A2AInstrumentor
    # ...
    class A2AClient:
        def __init__(self):
            # ...
            api_endpoint = os.getenv('OTLP_ENDPOINT', 'http://localhost:4318')
            Observe.init("A2A_Client", api_endpoint=api_endpoint)
            A2AInstrumentor().instrument()
    ```
    The `A2AClient` explicitly initializes `Observe` for its own operations, specifying a service name "A2A_Client" and an OTLP endpoint. Crucially, `A2AInstrumentor().instrument()` is called here to automatically instrument HTTP requests made by the A2A client, ensuring that A2A protocol interactions are captured as spans in traces.

## 3. Agent, Workflow, Task, and Tool Instrumentation

The `ioa_observe.sdk` provides decorators to automatically instrument key components of the agent's logic, turning them into observable units (spans in traces).

### `@agent` Decorator
The main agent class `HealthcareAgent` is decorated with `@agent`. This marks `HealthcareAgent` as a top-level observable entity, making its lifecycle and high-level operations traceable.

```python
@agent(name="healthcare_agent", description="healthcare voice agent", version="1.0.0", protocol="A2A")
class HealthcareAgent:
    # ...
```
This decorator captures the instantiation and execution of the agent, providing metadata like its name, description, version, and the protocol it primarily uses.

### `@workflow` Decorator
Workflows represent a sequence of related operations or a significant business process within the agent. The `_start_integrated_triage` and `_handle_triage_conversation` methods are decorated as workflows:

```python
@workflow(name="integrated_triage_workflow")
async def _start_integrated_triage(self):
    # ...

@workflow(name="triage_conversational_flow")
async def _handle_triage_conversation(self, user_input):
    # ...
```
These decorators ensure that the entire execution flow of starting a triage or handling a triage conversation is captured as a distinct workflow span, allowing for end-to-end tracing of these complex interactions.

### `@task` Decorator
The `@task` decorator is conceptually similar to `@workflow` but typically for smaller, more granular units of work within a workflow. The A2A protocol itself defines "tasks," and the `A2AInstrumentor` will likely create spans for these A2A tasks.

### `@tool` Decorator
Tools represent external capabilities or specific functions the agent can invoke. Several methods are decorated as `@tool`:

*   **Audio System Tools**:
    ```python
    @tool(name="listening_tool")
    async def listen(self, timeout=5):
        # ...
    @tool(name="speaking_tool")
    async def speak(self, text):
        # ...
    ```
    These capture the agent's interactions with the audio input/output, showing when the agent is listening or speaking.

*   **A2A Message Tool**:
    ```python
    @tool(name="a2a_message_tool")
    async def send_message(self, message_parts, task_id=None, context_id=None):
        # ...
    ```
    This instruments the `send_message` method of the `A2AClient`, making each message sent to the A2A service a traceable tool call.

*   **LLM Tool**:
    ```python
    @tool(name="llm_tool")
    async def process(self, user_input, session):
        # ...
    ```
    This instruments calls to the Large Language Model, tracking the prompts sent and responses received.

*   **Insurance Client Tools (MCP Protocol)**:
    ```python
    @tool(name="insurance_discovery_tool")
    async def discovery(self, name, dob, state):
        # ...
    @tool(name="insurance_eligibility_tool")
    async def eligibility(self, name, dob, subscriber_id, payer_name, provider_name):
        # ...
    ```
    These tools instrument the interactions with the Insurance Client, which uses the MCP (Managed Care Protocol) for discovery and eligibility checks. Each call to these methods will be captured as a tool invocation, providing visibility into the MCP service interactions.

## 4. A2A Protocol Observability

The `A2AClient` is specifically designed for A2A protocol interactions and includes dedicated instrumentation:

```python
from ioa_observe.sdk.instrumentations.a2a import A2AInstrumentor
# ...
class A2AClient:
    def __init__(self):
        # ...
        A2AInstrumentor().instrument()
```
The `A2AInstrumentor().instrument()` call is crucial. It automatically instruments HTTP requests made by the `requests` library (used by `A2AClient` for `_timed_request`), enriching them with A2A-specific context. This means that when the `A2AClient` sends messages or performs discovery, the underlying HTTP calls are automatically traced, and their spans are linked to the A2A task and message IDs, providing a clear view of the A2A communication flow within the overall trace.

## 5. Metrics

The agent also records specific metrics related to its availability and activity:

```python
from ioa_observe.sdk.metrics.agents.availability import agent_availability
# ...
class HealthcareAgent:
    async def start(self):
        # ...
        agent_availability.record_agent_heartbeat("healthcare_voice_agent")
        # ...
        if turn %5 ==0:
            agent_availability.record_agent_heartbeat("healthcare_voice_agent")
        # ...
        agent_availability.record_agent_activity("healthcare_voice_agent", success=False)
        # ...
        agent_availability.record_agent_activity("healthcare_voice_agent", success=True)
```
*   `agent_availability.record_agent_heartbeat("healthcare_voice_agent")`: This metric indicates that the agent is alive and operational. It's recorded at startup and periodically during the conversation (`every 5 turns`).
*   `agent_availability.record_agent_activity("healthcare_voice_agent", success=True/False)`: This metric tracks the agent's activity and whether a specific interaction was successful or not. It's used after processing user input to indicate successful processing or failures (e.g., unclear audio).

## 6. Session Tracing

The `session_start()` function is used within the `A2AClient.send_message` method to mark the beginning of a new session or a significant interaction within a trace.

```python
from ioa_observe.sdk.tracing import session_start
# ...
class A2AClient:
    async def send_message(self, message_parts, task_id=None, context_id=None):
        # ...
        session_start()
        # ...
```
This helps in organizing traces, especially in long-running conversations, by explicitly denoting the start of a new logical session or interaction within the tracing system.


 
