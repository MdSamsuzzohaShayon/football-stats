from datetime import datetime
from fastapi import HTTPException, Query, APIRouter, Depends
from sqlmodel import select
from src.config.redis import get_redis
from src.models import Match, MatchStats
from src.config.database import SessionDep
from src.utils.cache import (
    cache_match, get_cached_match, get_cached_matches,
    cache_matches
)
from typing import List, Annotated
from src.responses import MatchDetailResponse, MatchResponse
from sqlalchemy.orm import selectinload
from src.utils.helpers import MatchStatus
from src.utils.datetime import iso_date_to_offset

router = APIRouter()

# Store WebSocket connections in a list
connections = []


# Create match route (same as before)
@router.post("/", response_model=Match)
async def create_match(match: Match, session: SessionDep, redis=Depends(get_redis)) -> Match:
    try:
        # Add match to database
        session.add(match)
        session.commit()
        session.refresh(match)  # Ensure the match object has an ID

        # Create default match stats
        match_stats = MatchStats(
            match_id=match.id,  # Link to the match
            possession_team1=0,
            possession_team2=0,
            shots_team1=0,
            shots_team2=0,
            shots_on_target_team1=0,
            shots_on_target_team2=0,
            corners_team1=0,
            corners_team2=0,
            yellow_cards_team1=0,
            yellow_cards_team2=0
        )
        session.add(match_stats)
        session.commit()

        # Refresh the match to include relationship with stats
        session.refresh(match)

        # Cache the match in Redis
        await cache_match(redis, match)

        return match

    except Exception as e:
        session.rollback()  # Rollback any database changes on error
        raise HTTPException(status_code=500, detail=str(e))


# Fetch match by ID (New)
@router.get("/{match_id}", response_model=MatchDetailResponse)
async def get_match(match_id: int, session: SessionDep, redis=Depends(get_redis)) -> MatchDetailResponse:
    try:
        # Check Redis cache for the match
        match = await get_cached_match(redis, match_id)
        if match:
            return match

        # Fetch from the database if not in cache
        match = session.get(Match, match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Cache the match for future requests
        await cache_match(redis, match)
        return match

    except HTTPException as e:
        # Explicitly raised HTTPExceptions are propagated
        raise e

    except Exception as e:
        # Catch unexpected errors and log the exception
        print(f"Unexpected error occurred: {e}")  # Replace with logging in production
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[MatchResponse])
async def get_matches(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
        reload: bool = False,
        redis=Depends(get_redis),
) -> List[MatchResponse]:
    # Fetch cached matches if available
    if reload:
        matches = await get_cached_matches(redis)
        if matches:
            return matches

    # Fetch matches with related team1 and team2 fields
    statement = (
        select(Match)
        .options(selectinload(Match.team1), selectinload(Match.team2))
        .offset(offset)
        .limit(limit)
    )
    matches = session.exec(statement).all()

    if not matches:
        raise HTTPException(status_code=404, detail="No matches found")

    # Cache the match data if necessary
    await cache_matches(redis, matches)
    return matches  # Use from_orm to convert ORM models


@router.put("/{match_id}", response_model=Match)
async def update_match(
        match_id: int,
        session: SessionDep,
        match_update: Match = None,
        stats_update: MatchStats = None,
        redis=Depends(get_redis)
):
    try:
        # Fetch the match from the database
        match = session.get(Match, match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Update match fields (only if provided in the update request)
        if match_update.score_team1 is not None:
            match.score_team1 = match_update.score_team1
        if match_update.score_team2 is not None:
            match.score_team2 = match_update.score_team2
        if match_update.status is not None:
            match.status = match_update.status
        if match_update.start_time is not None:
            match.start_time = match_update.start_time
        if match_update.half_time is not None:
            match.half_time = match_update.half_time
        if match_update.second_start is not None:
            match.second_start = match_update.second_start
        if match_update.end_time is not None:
            match.end_time = match_update.end_time
        if match_update.team1_id is not None:
            match.team1_id = match_update.team1_id
        if match_update.team2_id is not None:
            match.team2_id = match_update.team2_id

        if match_update.status:
            match.status = match_update.status
            if match_update.status == MatchStatus.RUNNING and (match.start_time is None or match.start_time == ""):
                match.start_time = datetime.now()
            elif match_update.status == MatchStatus.HALF_TIME and match.half_time is None and match.half_time == "":
                match.half_time = datetime.now()
            elif match_update.status == MatchStatus.RUNNING and match.start_time is not None and match.start_time != "" and match.half_time is not None and match.half_time != "":
                match.second_start = datetime.now()
            elif match_update.status == MatchStatus.FULL_TIME and (match.end_time is None or match.end_time == ""):
                match.end_time = datetime.now()

        if match_update.start_time is not None and match_update.start_time != "":
            # Ensure MatchStats is created if the match is starting and doesn't already have stats
            match_stats = session.query(MatchStats).filter(MatchStats.match_id == match.id).first()
            if not match_stats:
                match_stats = MatchStats(match_id=match.id)
                session.add(match_stats)

        elif not match.half_time and match_update.start_time is not None and match.start_time != "":
            # Check start time according to start time set status
            half_time = iso_date_to_offset(match_update.start_time, MatchStatus.RUNNING.value)
            if half_time:
                match.start_time = half_time

        elif match_update.half_time is not None and match.half_time != "" and match.start_time:
            end_time = iso_date_to_offset(match_update.half_time, MatchStatus.HALF_TIME.value)
            if end_time:
                match.end_time = end_time

        # Update MatchStats fields if stats_update is provided
        if stats_update:
            match_stats = session.query(MatchStats).filter(MatchStats.match_id == match.id).first()
            if not match_stats:
                raise HTTPException(status_code=404, detail="MatchStats not found for this match")

            if stats_update.possession_team1 is not None:
                match_stats.possession_team1 = stats_update.possession_team1
            if stats_update.possession_team2 is not None:
                match_stats.possession_team2 = stats_update.possession_team2
            if stats_update.shots_team1 is not None:
                match_stats.shots_team1 = stats_update.shots_team1
            if stats_update.shots_team2 is not None:
                match_stats.shots_team2 = stats_update.shots_team2
            if stats_update.shots_on_target_team1 is not None:
                match_stats.shots_on_target_team1 = stats_update.shots_on_target_team1
            if stats_update.shots_on_target_team2 is not None:
                match_stats.shots_on_target_team2 = stats_update.shots_on_target_team2
            if stats_update.corners_team1 is not None:
                match_stats.corners_team1 = stats_update.corners_team1
            if stats_update.corners_team2 is not None:
                match_stats.corners_team2 = stats_update.corners_team2
            if stats_update.yellow_cards_team1 is not None:
                match_stats.yellow_cards_team1 = stats_update.yellow_cards_team1
            if stats_update.yellow_cards_team2 is not None:
                match_stats.yellow_cards_team2 = stats_update.yellow_cards_team2

            session.add(match_stats)

        # Commit changes to the database
        session.add(match)
        session.commit()
        session.refresh(match)

        # Cache the updated match details and publish updates
        await cache_match(redis, match)

        return match
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
