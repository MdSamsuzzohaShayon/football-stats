import json
import uuid
from redis.asyncio.client import Redis
from src.models import Player, Team, Match, MatchStats
from typing import List, Any, Optional

default_1_hr = 60 * 60  # Expire in 1 hour


# Cache player data in Redis
async def cache_player(redis: Redis, player: Player, ex: int = default_1_hr):
    player_dict = player.to_dict()
    player_dict["team"] = {"id": player.id, "name": player.name} if player is not None else None
    await redis.set(f"player:{player.id}", json.dumps(player_dict), ex=ex)


# Get cached player data from Redis
async def get_cached_player(redis: Redis, player_id: int):
    cached_data = await redis.get(f"player:{player_id}")
    if cached_data:
        return json.loads(cached_data)
    return None


# Cache team data in Redis
# async def cache_team(redis: Redis, team: Team, ex: int = default_1_hr):
#     await redis.set(f"team:{team.id}", team.json(), ex=ex)

async def cache_team(redis: Redis, team: Team, ex: int = default_1_hr):
    # Use a custom serialization method to get a JSON-serializable dictionary
    team_dict = team.to_dict()

    # Serialize the dictionary to JSON and cache it in Redis
    await redis.set(f"team:{team.id}", json.dumps(team_dict), ex=ex)


# Get cached team data from Redis
async def get_cached_team(redis: Redis, team_id: int) -> Optional[Team]:
    cached_data = await redis.get(f"team:{team_id}")
    if cached_data:
        team_dict = json.loads(cached_data)  # Convert JSON string back to Python dictionary

        # Ensure 'players' is a list of Player objects
        players = team_dict["players"]
        if isinstance(players, str):  # Deserialize only if it's a JSON string
            players = json.loads(players)
        team_dict["players"] = [Player(**player_data) for player_data in players]

        # Ensure 'all_matches' is a list of Match objects
        all_matches = team_dict["all_matches"]
        if isinstance(all_matches, str):  # Deserialize only if it's a JSON string
            all_matches = json.loads(all_matches)
        team_dict["all_matches"] = [Match(**match_data) for match_data in all_matches]

        # Reconstruct matches_as_team1 and matches_as_team2
        team_dict["matches_as_team1"] = [m for m in team_dict["all_matches"] if m.team1_id == team_id]
        team_dict["matches_as_team2"] = [m for m in team_dict["all_matches"] if m.team2_id == team_id]

        # Return the reconstructed Team model
        return Team(**team_dict)
    return None


# Cache multiple teams data in Redis
async def cache_teams(redis: Redis, teams: List[Team], ex: int = default_1_hr):
    # Create a dictionary where each key is the team ID and value is the serialized team data
    teams_dict = {f"team:{team.id}": json.dumps(team.to_dict()) for team in teams}

    # Use a pipeline to set multiple keys in Redis efficiently
    async with redis.pipeline() as pipe:
        for key, value in teams_dict.items():
            await pipe.set(key, value, ex=ex)
        await pipe.execute()


# Get cached multiple teams data from Redis
async def get_cached_teams(redis: Redis, offset: int = 0, limit: int = 100) -> Optional[List[Team]]:
    # Fetch all team keys
    keys = await redis.keys("team:*")

    # Apply sorting and slicing to keys for offset and limit
    keys = sorted(keys)[offset:offset + limit]

    if keys:
        # Use a pipeline to fetch the required teams efficiently
        async with redis.pipeline() as pipe:
            for key in keys:
                await pipe.get(key)
            cached_data_list = await pipe.execute()

        # Deserialize and reconstruct each team
        teams = []
        for cached_data in cached_data_list:
            if cached_data:
                team_dict = json.loads(cached_data)

                # Handle missing keys with default values
                players = team_dict.get("players", [])
                if isinstance(players, str):  # Deserialize only if it's a JSON string
                    players = json.loads(players)
                team_dict["players"] = [Player(**player_data) for player_data in players]

                all_matches = team_dict.get("all_matches", [])
                if isinstance(all_matches, str):  # Deserialize only if it's a JSON string
                    all_matches = json.loads(all_matches)
                team_dict["all_matches"] = [Match(**match_data) for match_data in all_matches]

                # Reconstruct matches_as_team1 and matches_as_team2
                team_dict["matches_as_team1"] = [
                    match for match in team_dict["all_matches"] if match.team1_id == team_dict.get("id")
                ]
                team_dict["matches_as_team2"] = [
                    match for match in team_dict["all_matches"] if match.team2_id == team_dict.get("id")
                ]

                # Reconstruct the Team model and append to the list
                teams.append(Team(**team_dict))

        return teams

    return None


# Cache match data in Redis and publish update
async def cache_match(redis: Redis, match: Match, ex: int = default_1_hr):
    match_dict = {
        "id": match.id,
        "team1": match.team1.to_dict() if match.team1 else None,
        "team2": match.team2.to_dict() if match.team2 else None,
        "score_team1": match.score_team1,
        "score_team2": match.score_team2,
        "status": match.status,
        "start_time": match.start_time,
        "half_time": match.half_time,
        "second_start": match.second_start,
        "end_time": match.end_time,
        "stats": match.stats.to_dict() if match.stats else None
    }

    # Cache the match details in Redis
    await redis.set(f"match:{match.id}", json.dumps(match_dict), ex=ex)

    # Publish match updates to Redis Pub/Sub
    await redis.publish(f"match_update:{match.id}", json.dumps(match_dict))


# Get cached match data from Redis
async def get_cached_match(redis: Redis, match_id: int) -> Optional[Match]:
    cached_data = await redis.get(f"match:{match_id}")
    if cached_data:
        # Deserialize the JSON string into a Python dictionary
        match_dict = json.loads(cached_data)

        # Reconstruct the nested Team and Player objects
        team1 = Team(
            id=match_dict["team1"]["id"],
            name=match_dict["team1"]["name"],
            city=match_dict["team1"]["city"],
            players=[Player(**player) for player in match_dict["team1"].get("players", [])]
        ) if match_dict["team1"] else None

        team2 = Team(
            id=match_dict["team2"]["id"],
            name=match_dict["team2"]["name"],
            city=match_dict["team2"]["city"],
            players=[Player(**player) for player in match_dict["team2"].get("players", [])]
        ) if match_dict["team2"] else None

        # Reconstruct MatchStats if it exists
        stats = MatchStats(
            id=match_dict["stats"].get("id", 0),
            match_id=match_dict["stats"].get("match_id", 0),
            possession_team1=match_dict["stats"].get("possession_team1", 0),
            possession_team2=match_dict["stats"].get("possession_team2", 0),
            shots_team1=match_dict["stats"].get("shots_team1", 0),
            shots_team2=match_dict["stats"].get("shots_team2", 0),
            shots_on_target_team1=match_dict["stats"].get("shots_on_target_team1", 0),
            shots_on_target_team2=match_dict["stats"].get("shots_on_target_team2", 0),
            corners_team1=match_dict["stats"].get("corners_team1", 0),
            corners_team2=match_dict["stats"].get("corners_team2", 0),
            yellow_cards_team1=match_dict["stats"].get("yellow_cards_team1", 0),
            yellow_cards_team2=match_dict["stats"].get("yellow_cards_team2", 0),
        ) if match_dict.get("stats") else None

        # Reconstruct and return the Match object
        return Match(
            id=match_dict["id"],
            team1=team1,
            team2=team2,
            score_team1=match_dict["score_team1"],
            score_team2=match_dict["score_team2"],
            status=match_dict["status"],
            start_time=match_dict["start_time"],
            half_time=match_dict["half_time"],
            second_start=match_dict["second_start"],
            end_time=match_dict["end_time"],
            stats=stats
        )
    return None

# Delete cached match data in Redis (New)
async def delete_cached_match(redis: Redis, match_id: int):
    await redis.delete(f"match:{match_id}")


# Cache multiple matches data in Redis
async def cache_matches(redis: Redis, matches: List[Match], ex: int = default_1_hr):
    """
    Cache match data in Redis with proper related fields for team1 and team2.

    Args:
        redis (Redis): The Redis instance to use for caching.
        matches (List[Match]): List of Match objects to cache.
        ex (int): Expiry time in seconds for the cached data.
    """
    matches_data = []
    for match in matches:
        match_data = {
            "id": match.id,
            "team1": match.team1.to_dict() if match.team1 else None,  # Ensure related fields are populated
            "team2": match.team2.to_dict() if match.team2 else None,
            "score_team1": match.score_team1,
            "score_team2": match.score_team2,
            "status": match.status,
        }
        matches_data.append(match_data)

    # Store the serialized data in Redis with expiration
    await redis.set("matches", json.dumps(matches_data), ex=ex)


# Get cached multiple matches data from Redis
async def get_cached_matches(redis: Redis):
    """
    Retrieve cached matches from Redis, populating teams with players as IDs.

    Args:
        redis (Redis): The Redis instance to fetch cached data.

    Returns:
        List[Match]: A list of Match objects with teams populated (players as IDs).
    """
    cached_data = await redis.get("matches")
    if cached_data:
        matches_data = json.loads(cached_data)
        matches = []
        for match_data in matches_data:
            team1 = Team(
                id=match_data["team1"]["id"],
                name=match_data["team1"]["name"],
                city=match_data["team1"]["city"],
                # players=match_data["team1"]["players"]  # Expecting a list of player IDs
            ) if match_data["team1"] else None

            team2 = Team(
                id=match_data["team2"]["id"],
                name=match_data["team2"]["name"],
                city=match_data["team2"]["city"],
                # players=match_data["team2"]["players"]  # Expecting a list of player IDs
            ) if match_data["team2"] else None

            match = Match(
                id=match_data["id"],
                team1=team1,
                team2=team2,
                score_team1=match_data["score_team1"],
                score_team2=match_data["score_team2"],
                status=match_data["status"]
            )
            matches.append(match)
        return matches
    return []



# Cache user session in Redis
async def cache_user_session(redis: Redis, user_id: int, ex: int = default_1_hr):
    session_token = str(uuid.uuid4())
    await redis.set(f"session:{session_token}", user_id, ex=ex)
    return session_token


# Get user from session token in Redis
async def get_cached_user(redis: Redis, session_token: str):
    user_id = await redis.get(f"session:{session_token}")
    return user_id


# Cache user's favorite matches (expires in 1 hour)
async def cache_favorite_matches(redis: Redis, user_id: int, matches: List[Match], ex: int = default_1_hr):
    matches_data = [match.json() for match in matches]
    await redis.set(f"user:{user_id}:favorites", json.dumps(matches_data), ex=ex)  # Cache for 1 hour


# Get cached user's favorite matches from Redis
async def get_cached_favorite_matches(redis: Redis, user_id: int):
    cached_data = await redis.get(f"user:{user_id}:favorites")
    if cached_data:
        return [Match.parse_raw(match) for match in json.loads(cached_data)]
    return None


# Add a favorite match to cache (Invalidate old cache)
async def add_favorite_match(redis: Redis, user_id: int, match: Match):
    cached_favorites = await get_cached_favorite_matches(redis, user_id)
    if cached_favorites:
        cached_favorites.append(match)
        await cache_favorite_matches(redis, user_id, cached_favorites)
    else:
        await cache_favorite_matches(redis, user_id, [match])


# Remove a favorite match from cache (Invalidate old cache)
async def remove_favorite_match(redis: Redis, user_id: int, match_id: int):
    cached_favorites = await get_cached_favorite_matches(redis, user_id)
    if cached_favorites:
        updated_favorites = [match for match in cached_favorites if match.id != match_id]
        await cache_favorite_matches(redis, user_id, updated_favorites)
