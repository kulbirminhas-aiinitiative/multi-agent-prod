"""
V2 API - Team Management
Create and manage teams with persona members
"""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends

from ...models import (
    CreateTeamRequest,
    TeamResponse,
    AddTeamMemberRequest,
    TeamMember,
)
from ...services import TeamService, get_team_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/teams", tags=["v2-teams"])


@router.post("", response_model=TeamResponse)
async def create_team(
    request: CreateTeamRequest,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Create a new team with persona members

    Example:
    ```json
    {
      "name": "API Design Team",
      "members": [
        {"persona": "architect", "provider": "claude_agent"},
        {"persona": "code_writer", "provider": "openai"}
      ]
    }
    ```
    """
    try:
        team = await team_service.create_team(request)
        return team
    except Exception as e:
        logger.error(f"Team creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    team_service: TeamService = Depends(get_team_service)
):
    """Get team details by ID"""
    team = await team_service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("", response_model=List[TeamResponse])
async def list_teams(
    team_service: TeamService = Depends(get_team_service)
):
    """List all teams"""
    teams = await team_service.list_teams()
    return teams


@router.post("/{team_id}/members", response_model=TeamMember)
async def add_team_member(
    team_id: UUID,
    request: AddTeamMemberRequest,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Add a persona to a team

    Example:
    ```json
    {
      "persona": "reviewer",
      "provider": "claude_agent",
      "system_prompt": "You are a meticulous code reviewer"
    }
    ```
    """
    try:
        member = await team_service.add_member(team_id, request)
        return member
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Add member failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}/members", response_model=List[TeamMember])
async def get_team_members(
    team_id: UUID,
    team_service: TeamService = Depends(get_team_service)
):
    """Get all members of a team"""
    try:
        members = await team_service.get_members(team_id)
        return members
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{team_id}")
async def delete_team(
    team_id: UUID,
    team_service: TeamService = Depends(get_team_service)
):
    """Delete a team"""
    success = await team_service.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"status": "deleted", "team_id": str(team_id)}
