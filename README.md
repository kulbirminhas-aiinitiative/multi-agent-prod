# Multi-Agent Service

Orchestrates teams of AI agents with different engagement modes.

## Features

- **Team Management**: Create and manage teams of AI agents with different personas
- **Multi-Agent Orchestration**: Support for multiple engagement modes:
  - Sequential: Agents respond one after another
  - Parallel: All agents respond simultaneously
  - Debate: Agents challenge each other's responses
  - Consensus: Iterate until agents reach agreement
- **RAG Integration**: Enhanced responses using knowledge base queries
- **Session Management**: Track conversation history and context

## Architecture

This service is a microservice that orchestrates multi-agent conversations by calling:
- **LLM Router (8001)**: For routing LLM requests to appropriate providers
- **RAG Service (8002)**: For knowledge base queries and context management

## API Endpoints

### Health
- `GET /health` - Health check

### Teams
- `POST /api/v2/teams` - Create a new team
- `GET /api/v2/teams` - List all teams
- `GET /api/v2/teams/{team_id}` - Get team details
- `DELETE /api/v2/teams/{team_id}` - Delete a team
- `POST /api/v2/teams/{team_id}/members` - Add member to team
- `GET /api/v2/teams/{team_id}/members` - Get team members

### Chat Sessions
- `POST /api/v2/chat/teams/{team_id}/sessions` - Create new session
- `POST /api/v2/chat/sessions/{session_id}/message` - Send message
- `GET /api/v2/chat/sessions/{session_id}` - Get session details
- `GET /api/v2/chat/sessions/{session_id}/messages` - Get messages
- `DELETE /api/v2/chat/sessions/{session_id}` - Delete session

## Running Locally

```bash
# Install dependencies
poetry install

# Run service
poetry run python -m multi_agent.main
```

## Running with Docker

```bash
# Build image
docker build -t multi-agent-service:latest .

# Run container
docker run -p 8003:8003 \
  -e LLM_ROUTER_URL=http://llm-router:8001 \
  -e RAG_SERVICE_URL=http://rag-service:8002 \
  multi-agent-service:latest
```

## Example Usage

### Create a Team

```bash
curl -X POST http://localhost:8003/api/v2/teams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Architecture Team",
    "description": "Team for system design",
    "members": [
      {"persona": "architect", "provider": "claude_agent"},
      {"persona": "security_expert", "provider": "openai"}
    ]
  }'
```

### Start a Chat Session

```bash
curl -X POST http://localhost:8003/api/v2/chat/teams/{team_id}/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_mode": "sequential",
    "max_iterations": 5,
    "enable_rag": true,
    "initial_message": {
      "content": "Design a microservices authentication system"
    }
  }'
```

## Configuration

Configure via environment variables or `.env` file. See `.env.example` for available options.
