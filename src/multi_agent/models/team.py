"""Team and Persona models"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TeamMemberConfig(BaseModel):
    """Configuration for a team member (persona)"""
    persona: str = Field(..., description="Persona name (e.g., 'architect', 'code_writer')")
    provider: str = Field(default="claude_agent", description="LLM provider")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific config")


class CreateTeamRequest(BaseModel):
    """Request to create a new team"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    members: list[TeamMemberConfig] = Field(..., min_items=1)


class Team(BaseModel):
    """Team model"""
    team_id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TeamMember(BaseModel):
    """Team member (persona) model"""
    id: int
    team_id: UUID
    persona: str
    provider: str
    system_prompt: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class TeamResponse(BaseModel):
    """Response with team details"""
    team_id: UUID
    name: str
    description: Optional[str] = None
    members: list[str]  # List of persona names
    created_at: datetime


class AddTeamMemberRequest(BaseModel):
    """Request to add a team member"""
    persona: str
    provider: str = "claude_agent"
    system_prompt: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
