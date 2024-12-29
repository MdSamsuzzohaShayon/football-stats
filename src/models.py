from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
from passlib.context import CryptContext
from datetime import datetime, timezone
from src.utils.helpers import MatchStatus, PlayerPosition

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




class BaseModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class UserMatchLink(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    match_id: int = Field(foreign_key="match.id")

    # Relationships
    user: "User" = Relationship(back_populates="favorite_matches")
    match: "Match" = Relationship(back_populates="favorited_by")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "match_id": self.match_id,
        }


class Team(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    city: Optional[str] = Field(default=None)

    players: list["Player"] = Relationship(back_populates="team")

    # Matches where the team is team1 or team2
    # Matches where the team is team1 or team2, specify foreign_keys
    matches_as_team1: List["Match"] = Relationship(
        back_populates="team1",
        sa_relationship_kwargs={"foreign_keys": "Match.team1_id"}
    )
    matches_as_team2: List["Match"] = Relationship(
        back_populates="team2",
        sa_relationship_kwargs={"foreign_keys": "Match.team2_id"}
    )

    @property
    def all_matches(self) -> List["Match"]:
        return self.matches_as_team1 + self.matches_as_team2

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "players": [player.to_dict() for player in self.players],
            "all_matches": [match.to_dict() for match in self.all_matches],
        }


class Player(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    birth: Optional[str] = Field(default=None, index=True)
    position: PlayerPosition = Field(default=PlayerPosition.LEFT_BACK, nullable=True)
    appearances: int = Field(default=0)
    goals: int = Field(default=0)
    assists: int = Field(default=0)
    team_id: int | None = Field(default=None, foreign_key="team.id")

    team: Team | None = Relationship(back_populates="players")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "birth": self.birth,
            "position": self.position,
            "appearances": self.appearances,
            "goals": self.goals,
            "assists": self.assists,
        }


class Match(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team1_id: int = Field(foreign_key="team.id")
    team2_id: int = Field(foreign_key="team.id")
    score_team1: int = Field(default=0)
    score_team2: int = Field(default=0)
    status: MatchStatus = Field(default=MatchStatus.NOT_STARTED) # Half-time / Full-Time / Not Started / Running
    start_time: Optional[str] = Field(nullable=True)
    half_time: Optional[str] =  Field(nullable=True)
    second_start: Optional[str] =  Field(nullable=True)
    end_time: Optional[str] =  Field(nullable=True)

    # Relationships for teams in the match
    team1: Optional[Team] = Relationship(
        back_populates="matches_as_team1",
        sa_relationship_kwargs={"foreign_keys": "Match.team1_id"}
    )
    team2: Optional[Team] = Relationship(
        back_populates="matches_as_team2",
        sa_relationship_kwargs={"foreign_keys": "Match.team2_id"}
    )

    # Relationships for users favoriting this match
    favorited_by: List["UserMatchLink"] = Relationship(back_populates="match")
    stats: Optional["MatchStats"] = Relationship(back_populates="match")

    def to_dict(self):
        return {
            "id": self.id,
            "team1_id": self.team1_id,
            "team2_id": self.team2_id,
            "score_team1": self.score_team1,
            "score_team2": self.score_team2,
            "status": self.status,
            "start_time": self.start_time,
            "half_time": self.half_time,
            "second_start": self.half_time,
            "end_time": self.end_time,
        }


class MatchStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)  # Make id optional
    match_id: Optional[int] = Field(default=None, foreign_key="match.id", index=True)  # Optional
    possession_team1: Optional[int] = Field(default=0)
    possession_team2: Optional[int] = Field(default=0)
    shots_team1: Optional[int] = Field(default=0)
    shots_team2: Optional[int] = Field(default=0)
    shots_on_target_team1: Optional[int] = Field(default=0)
    shots_on_target_team2: Optional[int] = Field(default=0)
    corners_team1: Optional[int] = Field(default=0)
    corners_team2: Optional[int] = Field(default=0)
    yellow_cards_team1: Optional[int] = Field(default=0)
    yellow_cards_team2: Optional[int] = Field(default=0)

    # Relationships
    match: Optional["Match"] = Relationship(back_populates="stats")

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "possession_team1": self.possession_team1,
            "possession_team2": self.possession_team2,
            "shots_team1": self.shots_team1,
            "shots_team2": self.shots_team2,
            "shots_on_target_team1": self.shots_on_target_team1,
            "shots_on_target_team2": self.shots_on_target_team2,
            "corners_team1": self.corners_team1,
            "corners_team2": self.corners_team2,
            "yellow_cards_team1": self.yellow_cards_team1,
            "yellow_cards_team2": self.yellow_cards_team2,
        }


class User(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

    # Relationships
    favorite_matches: List["UserMatchLink"] = Relationship(back_populates="user")

    def set_password(self, password: str):
        """Hashes and sets the user's password."""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verifies the provided password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
        }
