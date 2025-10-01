# Customer Support— Multi-Agent Systems

The Customer Support repository contains a collection of multi-agent system (MAS) applications built with [AGNTCY components](https://github.com/agntcy) — an open-source framework. These projects demonstrate how AI agents can collaborate to automate end-to-end customer support workflows across different verticals — such as healthcare, retail, and insurance — using standardized protocols and orchestration patterns.

## Motivation

### Why Customer Support?
Customer support is one of the highest-value domains for AI agents:
- Customer-facing tasks are structured, repetitive, and time-sensitive.
- Multi-agent systems (MAS) provide a natural fit for triage, task routing, and resolution workflows.

### Repository Structure
Each folder implements a customer support MAS application for a specific vertical:
- /agentic-healthcare-booking-app → Multi-agent system for healthcare appointment scheduling, symptom triage, and insurance queries.

# Agentic Healthcare Booking App

The [agentic-healthcare-booking-app repository](https://github.com/techm-2025/customer-support/tree/main/agentic-healthcare-booking-app) is a reference implementation of a Healthcare Booking Multi-Agent System (MAS). It showcases how multiple AI agents can collaborate to handle appointment scheduling, symptom triage, and insurance policy management.

Built with [AGNTCY components](https://github.com/agntcy) and open-source agentic AI frameworks, this project demonstrates practical patterns for agent-to-agent communication, orchestration, identity, and observability in a real-world vertical.

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
- **MAS Development** → Core multi-agent architecture
- **Agent-to-Agent (A2A) Messaging** → Coordination between agents
- **MCP Protocol Integration** → Standardized tool calls and context sharing
- **Identity Layer** → Authentication & TBAC
- **Observability Stack** → Runtime monitoring and schema validation

## Installation
**1. Clone the repository**
- git clone [repository-url](https://github.com/techm-2025/customer-support/tree/main/agentic-healthcare-booking-app)
- cd agentic-healthcare-booking-app

**2. Install dependencies**
- pip install -r requirements.txt
- npm install

**3. Configure environment**
- cp .env.example .env # Edit .env with your configuration

### Next Steps
- Review the [AGNTCY documentation](https://docs.agntcy.org) for details on MAS components.
- Explore the /agents directory to see implementations of booking, triage, and insurance agents.
- Extend the system with new agents or protocols to test interoperability.

## Contributing
Contributions are welcome! Please open issues or pull requests to discuss improvements, bug fixes, or new agent integrations.
