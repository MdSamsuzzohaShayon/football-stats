from fastapi import Depends, APIRouter, HTTPException, Query
from sqlmodel import select
from src.responses import PlayerResponse, SimplePlayerResponse
from typing import List, Optional

from src.utils.cache import (
    cache_player, get_cached_player
)
from src.config.database import SessionDep
from src.config.redis import get_redis
from src.models import Player, Team

router = APIRouter()


# Route to fetch all players with optional filters
@router.get("/", response_model=List[PlayerResponse])
async def get_players(
        session: SessionDep,
        redis=Depends(get_redis),
        team_id: Optional[int] = Query(None, description="Filter players by team ID"),
        match_id: Optional[int] = Query(None, description="Filter players by match ID"),

) -> List[PlayerResponse]:
    # Base query to select all players
    query = select(Player)

    # Apply filters based on query parameters
    if team_id:
        query = query.where(Player.team_id == team_id)

    if match_id:
        query = query.where(
            (Player.team.has(Team.matches_as_team1.any(id=match_id))) |
            (Player.team.has(Team.matches_as_team2.any(id=match_id)))
        )

    # Execute the query and fetch results
    players = session.exec(query).all()

    if not players:
        raise HTTPException(status_code=404, detail="No players found for the given filters")

    return players


# Route to fetch a single player by ID with team details
@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, session: SessionDep, redis=Depends(get_redis)) -> PlayerResponse:
    # Try to get cached player first
    cached_player = await get_cached_player(redis, player_id)
    if cached_player:
        return cached_player

    # Fetch the player from the database
    statement = select(Player).where(Player.id == player_id)
    player_result = session.exec(statement).first()

    if not player_result:
        raise HTTPException(status_code=404, detail="Player not found")

    # Fetch the team of the player using team_id (if not already loaded via relationship)
    if player_result.team_id and not player_result.team:
        statement = select(Team).where(Team.id == player_result.team_id)
        team_result = session.exec(statement).first()

        if team_result:
            player_result.team = team_result  # Set the team data in the player object

    # Cache the player data
    await cache_player(redis, player_result)

    return player_result


# Create player route (same as before)
@router.post("/", response_model=SimplePlayerResponse)
async def create_player(player: Player, session: SessionDep, redis=Depends(get_redis)) -> SimplePlayerResponse:
    try:
        session.add(player)
        session.commit()
        session.refresh(player)
        await cache_player(redis, player)
        return player
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
