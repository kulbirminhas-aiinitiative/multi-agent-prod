"""
Team Service
Business logic for team and member management
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..models import (
    Team,
    TeamMember,
    TeamResponse,
    CreateTeamRequest,
    AddTeamMemberRequest,
)

logger = logging.getLogger(__name__)


class TeamService:
    """
    Service for managing teams and their members

    For MVP: In-memory storage
    TODO: Add PostgreSQL + Redis persistence
    """

    def __init__(self):
        # In-memory storage for MVP
        self.teams: dict[UUID, Team] = {}
        self.members: dict[UUID, List[TeamMember]] = {}
        self._member_id_counter = 1

        logger.info("TeamService initialized (in-memory mode)")

    async def create_team(self, request: CreateTeamRequest) -> TeamResponse:
        """Create a new team with members"""

        # Create team
        team = Team(
            name=request.name,
            description=request.description,
        )

        self.teams[team.team_id] = team
        self.members[team.team_id] = []

        # Add members
        for member_config in request.members:
            member = TeamMember(
                id=self._member_id_counter,
                team_id=team.team_id,
                persona=member_config.persona,
                provider=member_config.provider,
                system_prompt=member_config.system_prompt,
                config=member_config.config,
            )
            self._member_id_counter += 1
            self.members[team.team_id].append(member)

        logger.info(f"Created team: {team.name} ({team.team_id}) with {len(request.members)} members")

        return TeamResponse(
            team_id=team.team_id,
            name=team.name,
            description=team.description,
            members=[m.persona for m in self.members[team.team_id]],
            created_at=team.created_at,
        )

    async def get_team(self, team_id: UUID) -> Optional[TeamResponse]:
        """Get team by ID"""

        team = self.teams.get(team_id)
        if not team:
            return None

        members = self.members.get(team_id, [])

        return TeamResponse(
            team_id=team.team_id,
            name=team.name,
            description=team.description,
            members=[m.persona for m in members],
            created_at=team.created_at,
        )

    async def list_teams(self) -> List[TeamResponse]:
        """List all teams"""

        teams = []
        for team in self.teams.values():
            members = self.members.get(team.team_id, [])
            teams.append(
                TeamResponse(
                    team_id=team.team_id,
                    name=team.name,
                    description=team.description,
                    members=[m.persona for m in members],
                    created_at=team.created_at,
                )
            )

        return teams

    async def add_member(self, team_id: UUID, request: AddTeamMemberRequest) -> TeamMember:
        """Add a member to a team"""

        if team_id not in self.teams:
            raise ValueError(f"Team not found: {team_id}")

        # Check if persona already exists
        existing = [m for m in self.members[team_id] if m.persona == request.persona]
        if existing:
            raise ValueError(f"Persona already exists in team: {request.persona}")

        member = TeamMember(
            id=self._member_id_counter,
            team_id=team_id,
            persona=request.persona,
            provider=request.provider,
            system_prompt=request.system_prompt,
            config=request.config,
        )
        self._member_id_counter += 1

        self.members[team_id].append(member)

        logger.info(f"Added member to team {team_id}: {request.persona}")

        return member

    async def get_members(self, team_id: UUID) -> List[TeamMember]:
        """Get all members of a team"""

        if team_id not in self.teams:
            raise ValueError(f"Team not found: {team_id}")

        return self.members.get(team_id, [])

    async def get_member(self, team_id: UUID, persona: str) -> Optional[TeamMember]:
        """Get a specific team member by persona"""

        members = self.members.get(team_id, [])
        for member in members:
            if member.persona == persona:
                return member
        return None

    async def delete_team(self, team_id: UUID) -> bool:
        """Delete a team"""

        if team_id not in self.teams:
            return False

        del self.teams[team_id]
        del self.members[team_id]

        logger.info(f"Deleted team: {team_id}")

        return True

    async def update_team(
        self,
        team_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[TeamResponse]:
        """Update team details"""

        team = self.teams.get(team_id)
        if not team:
            return None

        if name:
            team.name = name
        if description is not None:
            team.description = description

        team.updated_at = datetime.now()

        logger.info(f"Updated team: {team_id}")

        return await self.get_team(team_id)


# Global service instance
_team_service = None


def get_team_service() -> TeamService:
    """Get global team service instance"""
    global _team_service
    if _team_service is None:
        _team_service = TeamService()
    return _team_service
