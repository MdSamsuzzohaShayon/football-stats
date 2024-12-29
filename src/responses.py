from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.utils.helpers import PlayerPosition, MatchStatus


class CommonModel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime


# Player response model (includes only minimal team details)
class SimpleTeamResponse(CommonModel):
    name: str


# Simplified player model for embedding in team response
class SimplePlayerResponse(CommonModel):
    name: str
    position: Optional[PlayerPosition]
    birth: str
    appearances: int
    goals: int
    assists: int


class MatchStatsResponse(BaseModel):
    id: int
    match_id: int
    possession_team1: Optional[int]
    possession_team2: Optional[int]
    shots_team1: Optional[int]
    shots_team2: Optional[int]
    shots_on_target_team1: Optional[int]
    shots_on_target_team2: Optional[int]
    corners_team1: Optional[int]
    corners_team2: Optional[int]
    yellow_cards_team1: Optional[int]
    yellow_cards_team2: Optional[int]

    class Config:
        from_attributes = True


class SimpleMatchResponse(CommonModel):
    score_team1: int
    score_team2: int
    status: MatchStatus
    start_time: Optional[str]
    half_time: Optional[str]
    second_start: Optional[str]
    end_time: Optional[str]


# Player response model (with minimal team info to avoid recursion)
class PlayerResponse(CommonModel):
    name: str
    birth: Optional[str]
    position: Optional[PlayerPosition]
    appearances: int
    goals: int
    assists: int

    team: Optional[SimpleTeamResponse]  # Avoid full team details to break recursion

    class Config:
        from_attributes = True


# Team response model (includes a list of simple player details)
class TeamResponse(CommonModel):
    name: str
    city: Optional[str]

    players: List[SimplePlayerResponse]  # Avoid full player details to break recursion
    all_matches: List[SimpleMatchResponse]

    class Config:
        from_attributes = True


class MatchResponse(SimpleMatchResponse):
    team1: Optional[SimpleTeamResponse]  # Nested response for team1
    team2: Optional[SimpleTeamResponse]  # Nested response for team2

    class Config:
        from_attributes = True


class MatchDetailResponse(SimpleMatchResponse):
    stats: Optional[MatchStatsResponse] = None
    team1: Optional[TeamResponse]  # Nested response for team1
    team2: Optional[TeamResponse]  # Nested response for team2

    class Config:
        from_attributes = True
