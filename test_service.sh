#!/bin/bash
# Test script for multi-agent-service

set -e

echo "Testing Multi-Agent Service..."
echo "================================"

# Test 1: Health check
echo -e "\n1. Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8003/health)
echo "Response: $HEALTH"

# Test 2: Create a team
echo -e "\n2. Creating a test team..."
TEAM_RESPONSE=$(curl -s -X POST http://localhost:8003/api/v2/teams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Architecture Team",
    "description": "System design experts",
    "members": [
      {"persona": "architect", "provider": "claude_agent"},
      {"persona": "security_expert", "provider": "openai"}
    ]
  }')
echo "Response: $TEAM_RESPONSE"

# Extract team_id
TEAM_ID=$(echo $TEAM_RESPONSE | jq -r '.team_id')
echo "Team ID: $TEAM_ID"

# Test 3: List teams
echo -e "\n3. Listing all teams..."
curl -s http://localhost:8003/api/v2/teams | jq .

# Test 4: Get team details
echo -e "\n4. Getting team details..."
curl -s http://localhost:8003/api/v2/teams/$TEAM_ID | jq .

# Test 5: Get team members
echo -e "\n5. Getting team members..."
curl -s http://localhost:8003/api/v2/teams/$TEAM_ID/members | jq .

# Test 6: Create a chat session (will fail if LLM router is not available, but that's expected)
echo -e "\n6. Creating a chat session..."
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8003/api/v2/chat/teams/$TEAM_ID/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_mode": "sequential",
    "max_iterations": 5,
    "enable_rag": false
  }')
echo "Response: $SESSION_RESPONSE"

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# Test 7: Get session details
echo -e "\n7. Getting session details..."
curl -s http://localhost:8003/api/v2/chat/sessions/$SESSION_ID | jq .

echo -e "\n================================"
echo "All basic tests completed!"
