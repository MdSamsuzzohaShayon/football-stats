import json
from sqlmodel import SQLModel
from fastapi import Depends
from typing import Annotated
from sqlmodel import Session, create_engine
from src.models import User, Team, Player, Match, MatchStats, UserMatchLink  # Import your models
from datetime import datetime

# Database connection URL
mysql_url = f"mysql+mysqlconnector://shayon:Test1234@localhost/football_stats"
engine = create_engine(mysql_url, echo=True)


# Function to drop and recreate database tables
def reset_database():
    print("Deleting existing tables...")
    SQLModel.metadata.drop_all(engine)  # Drop all existing tables
    print("Creating new tables...")
    SQLModel.metadata.create_all(engine)  # Recreate tables


# Dependency to get session
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# Function to parse datetime into MySQL-compatible format
def parse_datetime(value: str) -> str:
    """Parse ISO 8601 datetime to MySQL DATETIME format."""
    try:
        # Parse the ISO 8601 datetime string
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Convert to MySQL DATETIME format
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value  # Return the original value if parsing fails


# Function to load data from JSON and seed the database
def seed_database_from_json(json_file_path: str):
    with open(json_file_path, "r") as f:
        data = json.load(f)

    with Session(engine) as session:
        # Seed users
        if "users" in data:
            for user_data in data["users"]:
                user = User(**user_data)
                session.add(user)

        # Seed teams
        if "teams" in data:
            for team_data in data["teams"]:
                team = Team(**team_data)
                session.add(team)

        # Seed players
        if "players" in data:
            for player_data in data["players"]:
                player = Player(**player_data)
                session.add(player)

        # Seed matches
        if "matches" in data:
            for match_data in data["matches"]:
                if "start_time" in match_data:
                    match_data["start_time"] = parse_datetime(match_data["start_time"])
                if "half_time" in match_data:
                    match_data["half_time"] = parse_datetime(match_data["half_time"])
                if "second_start" in match_data:
                    match_data["second_start"] = parse_datetime(match_data["second_start"])
                if "end_time" in match_data:
                    match_data["end_time"] = parse_datetime(match_data["end_time"])
                match = Match(**match_data)
                session.add(match)

        # Seed match stats
        if "match_stats" in data:
            for stats_data in data["match_stats"]:
                stats = MatchStats(**stats_data)
                session.add(stats)

        # Seed user-match links
        if "user_match_links" in data:
            for link_data in data["user_match_links"]:
                link = UserMatchLink(**link_data)
                session.add(link)

        # Commit all changes
        session.commit()


# Example JSON file path
json_file_path = "src/seed_data.json"

# Call the seeding function
if __name__ == "__main__":
    reset_database()
    seed_database_from_json(json_file_path)
