from typing import List, Annotated

from fastapi import Depends, APIRouter, HTTPException, Query
from sqlmodel import select

from src.utils.cache import cache_team, get_cached_team, cache_teams, get_cached_teams
from src.config.database import SessionDep
from src.config.redis import get_redis
from src.models import Team
from src.responses import TeamResponse

router = APIRouter()


# Route to fetch a single team by ID with relationships
@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, session: SessionDep, redis=Depends(get_redis)) -> TeamResponse:
    try:
        # Try to get cached team first
        cached_team = await get_cached_team(redis, team_id)
        if cached_team:
            return cached_team

        # Fetch the team from the database with related fields
        statement = select(Team).where(Team.id == team_id)
        team_result = session.exec(statement).first()

        if not team_result:
            raise HTTPException(status_code=404, detail="Team not found")

        # Cache the team data in Redis
        await cache_team(redis, team_result)

        return team_result
    except Exception as e:
        print(e)


# Route to fetch multiple teams with relationships
@router.get("/", response_model=List[TeamResponse])
async def get_teams(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        redis=Depends(get_redis)
) -> List[TeamResponse]:
    # Attempt to get cached data
    teams = await get_cached_teams(redis, offset, limit)
    if teams:
        return teams

    # Fetch teams with players and matches populated
    statement = (
        select(Team)
        .offset(offset)
        .limit(limit)
    )
    teams = session.exec(statement).all()

    if not teams:
        raise HTTPException(status_code=404, detail="No teams found")

    # Cache the team data
    await cache_teams(redis, teams)

    # Return teams with all related fields populated
    return teams


# Create team route (same as before)
@router.post("/", response_model=Team)
async def create_team(team: Team, session: SessionDep, redis=Depends(get_redis)) -> Team:
    try:
        session.add(team)
        session.commit()
        session.refresh(team)
        await cache_team(redis, team)
        return team
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
