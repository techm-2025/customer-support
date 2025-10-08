# Healthcare Booking Application

A comprehensive healthcare booking and management system built with autonomous agents for insurance verification, medical triage, and voice interactions.

## Project Structure

### `/documentation`
Project documentation and guides. Contains the main README and other supporting documentation files.

### `/insurance-agent`
Insurance verification and benefits checking agent powered by Infinitus API.

- **`infinitus/`** - Core insurance agent implementation
  - `va_mcp.py` - Model Context Protocol integration for Insurance API with voice-agent communication
  - `README.md` - Detailed insurance agent API - MCP documentation

### `/triage_agent`
Medical symptom triage system that assesses patient symptoms and provides preliminary medical assessment and provides recommendations.

- **`infermedica/`** - Symptom triaging powered by Infermedica API
  - **`agntcy/`** - Identity and Observability components
    - **`observe_config/`** - Complete observability stack configuration
      - **`deploy/`** - deployment configurations
        - `clickhouse/` - Time-series analytics database setup
        - `grafana/` - Visualization dashboards and datasources
        - `nginx/` - Reverse proxy and load balancer configs
        - `otel/` - OpenTelemetry collector for distributed tracing
        - `scripts/` - Deployment automation scripts (deploy, backup, update)
        - `docker-compose.yml` - Full observability stack orchestration
      - `observe_config.py` - Observability configuration management
    - **`test-client/`** - Testing utilities
      - `identity_client.py` - Identity service test client
      - `triage_client.py` - Triage service test client
    - `identity_observe_wrapper_service.py` - Identity wrapped A2a service with observability hooks
  
- **`medical-triage/`** - Standalone triage service
  - `triagev2.py` - Core triage logic and API endpoints
  - `agent-card.json` - Agent metadata and capabilities manifest
  - `Dockerfile` - Containerization configuration
  - `docker-compose.yml` - Service orchestration
  - `requirements.txt` - Python dependencies

### `/voice-agent`
Voice interaction agent for patient communication via phone or voice interface.

- **`agntcy/`** - Voice agent implementation
  - `va_identity_observe.py` - Identity, observe components for voice-agent
  
- **`unit-tests/`** - Testing suite
  - `a2a_client.py` - Agent-to-agent communication test client
  - `http_client.py` - HTTP API test client

- **Core MCP Servers:**
  - `va_a2a_mcp.py` - Agent-to-agent,  Model Context Protocol clients with voice-agent communication
  - `va_http_mcp.py` - HTTP-based Medical triage, Model Context Protocol based Insurance clients with voice-agent communication

## Getting Started

Each component has its own README with detailed setup instructions:

1. **Insurance Agent** - See `/insurance-agent/README.md`
2. **Triage Agent** - See `/triage_agent/README.md` and `/triage_agent/medical-triage/README.md`
3. **Voice Agent** - See `/voice-agent/README.md`
4. **Observe Stack** - See `/triage_agent/infermedica/agntcy/observe_config/README.md`

## Key Technologies

- **MCP (Model Context Protocol)** - Agent communication standard
- **Infermedica API** - Medical symptom analysis
- **Infinitus API** - Insurance benefits verification
- **OpenTelemetry** - Distributed tracing and observability
- **ClickHouse** - Analytics database
- **Grafana** - Monitoring dashboards
- **Docker** - Containerization and orchestration
- **Identity** - Task-based Access Control and enforcing policies on agent communication

## Agent Communication

Agents communicate with each other, enabling:
- Model Context Protocol (MCP) tool calls
- Seamless agent-to-agent (A2A) interactions
- Standardized HTTP-based APIs
- Identity management and authentication
- Distributed tracing across agent boundaries

## 📝 License

Apache 2.0 License
