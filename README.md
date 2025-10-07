# Customer Support— Multi-Agent Systems

The Customer Support repository contains a collection of multi-agent system (MAS) applications built with [AGNTCY components](https://github.com/agntcy) — an open-source framework. These projects demonstrate how AI agents can collaborate to automate end-to-end customer support workflows across different verticals — such as healthcare, retail, and insurance — using standardized protocols and orchestration patterns.

## Motivation

### Why Customer Support?
Customer support is one of the highest-value domains for AI agents:
- Customer-facing tasks are structured, repetitive, and time-sensitive.
- Multi-agent systems (MAS) provide a natural fit for triage, task routing, and resolution workflows.

### Repository Structure
Each folder implements a customer support MAS application for a specific vertical:
- /healthcare-booking-app → Multi-agent system for healthcare appointment scheduling, symptom triage, and insurance queries.

# Healthcare Booking App

The [healthcare-booking-app repository](https://github.com/techm-2025/customer-support/tree/main/healthcare-booking-app) is a reference implementation of a Healthcare Booking Multi-Agent System (MAS). It showcases how multiple AI agents can collaborate to handle appointment scheduling, symptom triage, and insurance policy management.

Built with [AGNTCY components](https://github.com/agntcy) — an open-source framework, this project demonstrates practical patterns for agent-to-agent communication, orchestration, identity, and observability in a real-world vertical.

## Domain Relevance
Healthcare is a structured, high-stakes environment that highlights the need for multi-agent collaboration. Appointment workflows, triage decisions, and insurance queries are concrete examples of tasks where specialized agents must coordinate seamlessly.

## Use Cases
- Appointment Scheduling → Automating booking workflows across providers.
- Symptom Triage → Routing patients based on condition severity.
- Insurance Policy Management → Validating coverage and handling pre-approvals.

## Research & Experimentation Value
This repository provides a sandbox for MAS developers and researchers to:
- Evaluate agent-to-agent protocols (A2A, MCP)
- Prototype orchestration strategies for distributed decision-making
- Explore task-based access control (TBAC) and agent identity management
- Test observability pipelines (metrics, schema validation, runtime monitoring)

## Integration Opportunities
By implementing with AGNTCY standards, the system demonstrates:
- Discovery & registration in a shared agent directory
- Cross-framework interoperability for heterogeneous agents
- Context exchange and authenticated communication between agents
- Reusability of components across healthcare and other verticals

# Key Technologies
- **AGNTCY: Internet of Agents**
  -  Open-source framework enabling discovery, orchestration, and collaboration across agents built on different stacks.
- **MCP (Model Context Protocol)**
  - Protocol for structured inter-agent communication and tool calls.
- **Agent-to-Agent (A2A) Messaging**
  - Peer-to-peer agent communication for distributed workflows.
- **AGNTCY: Core Components**
  - **OASF & Agent Directory** → Registry and discovery
  - **Identity** → Authentication, agent cards, TBAC
  - **Observability** → Metrics, schema validation, runtime monitoring

# Implementation Overview

![arch3](https://github.com/user-attachments/assets/c63fa02d-b5ce-4380-8a4a-2d636c4c5287)

### Architecture Components:

**AGNTCY Identity Service:**
A centralized authentication and authorization service that manages identity verification and enforces Task-Based Access Control (TBAC) policies across all the agents in the system.
**OASF Voice Agent:**
An Open Agentic Schema Framework (OASF) voice enabled agent that processes user voice inputs, interprets healthcare requests, and coordinates with other agents to facilitate medical triaging, insurance verification and appointment scheduling.
**A2A  Symptom Triage Wrapper:**
A wrapper service that interfaces between the voice agent and the Infermedica Symptom Triage Agent, translating A2A messages and managing the symptom triage workflow.
**Infinitus Insurance Agent:**
A partner agent that handles insurance discovery and benefits eligibility verification through the MCP protocol integration with the Voice Agent.
**Infermedica Symptom Triage Agent:**
A medical AI agent that performs symptom analysis and preliminary diagnosis, accessed via REST API to provide medical triage assessment for healthcare booking.
**AGNTCY Observe:**
Observability monitoring tracks agent interactions, and provide runtime insights.

### Flow Descriptions:

**1. User Interaction:**
The user initiates a voice conversation with the OASF Voice Agent, providing healthcare-related queries like symptoms, demographics, appointment preferences etc., that trigger the healthcare booking workflow.
**2. Authorize & Policy Enforcement:**
The Voice Agent authenticates with the AGNTCY Identity service and retrives applicable TBAC policies to determine what tasks and resources the agent is authorized to access, here the A2A Symptom Triage Wrapper.
**3. A2A Communication:**
After successful TBAC authorization, the Voice Agent sends A2A messages to the A2A Symptom Triage Wrapper, enabling coordinated symptom assessment.
**4. REST/HTTP API Call:**
The A2A Symptom Triage Wrapper makes external API caclls to the Infermedica Symptom Triage Agent, sending user symptom data and receiving recommendations for appropriate care routing.
**5. Authorize & Policy Enforcement:**
The A2A Symptom Triage authenticates with the AGNTCY Identity service and retrives applicable TBAC policies to determine what tasks and resources the agent is authorized to access, here the OASF Voice Agent.
**6. A2A Communication:**
After successful TBAC authorization, the A2A Symptom Triage Wrapper sends A2A messages to the Voice Agent, enabling coordinated symptom assessment.
**7. MCP Tool Call:**
The Voice Agent invokes the Infinitus Insurance Agent through standardized MCP tool calls to verify patient insurance discovery, check benefits eligibility before scheduling appointments.

- **MAS Development** → Core multi-agent architecture
- **Agent-to-Agent (A2A) Messaging** → Coordination between agents
- **MCP Protocol Integration** → Standardized tool calls and context sharing
- **Identity Layer** → Authentication & TBAC
- **Observability Stack** → Runtime monitoring and schema validation

## Installation
**1. Clone the repository**
- git clone [repository-url](https://github.com/techm-2025/customer-support/tree/main/healthcare-booking-app)
- cd healthcare-booking-app

**2. Install dependencies**
- pip install -r requirements.txt
- npm install

**3. Configure environment**
- cp .env.example .env # Edit .env with your configuration

## Next Steps
- Review the [AGNTCY documentation](https://docs.agntcy.org) for details on MAS components.
- Explore the /agents directory to see implementations of booking, triage, and insurance agents.
- Extend the system with new agents or protocols to test interoperability.

## References
1. AGNTCY documentation - https://docs.agntcy.org
2. AGNTCY github repository - https://github.com/agntcy

## Contributing
Contributions are welcome! Please open issues or pull requests to discuss improvements, bug fixes, or new agent integrations.
