from fastapi import APIRouter, HTTPException, Depends
from src.models import User, Match, UserMatchLink
from sqlmodel import select
from src.config.database import SessionDep
from src.schema import UserCreate, UserLogin
from src.utils.cache import cache_user_session, get_cached_user, remove_favorite_match, get_cached_favorite_matches
from src.config.redis import get_redis
from fastapi_limiter.depends import RateLimiter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Register a new user
@router.post("/register", response_model=dict)
async def register_user(user_data: UserCreate, session: SessionDep):
    # Use SQLModel's select to check if the user already exists
    statement = select(User).where(User.username == user_data.username)
    session_user = session.exec(statement).first()  # Use .first() to get the single result

    # Debug logging to check the session_user value
    logger.debug(f"Checking for existing user: {user_data.username}, Found: {session_user}")

    if session_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create a new user
    user = User(username=user_data.username)
    user.set_password(user_data.password)  # Hash the password

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        # await cache_user(redis, user)  # Cache the newly created user
        return {"msg": "User registered successfully", "user": user.username}
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Login and generate a session
@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=10))])  # Example: 5 requests per 10 seconds
async def login_user(user_data: UserLogin, session: SessionDep, redis=Depends(get_redis)):
    user = session.exec(select(User).where(User.username == user_data.username)).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Save session token in Redis with user id
    session_token = await cache_user_session(redis, user.id)
    return {"session_token": session_token}


# Get the current user from session
async def get_current_user(session_token: str, session: SessionDep, redis=Depends(get_redis)):
    user_id = await get_cached_user(redis, session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    user = session.query(User).get(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Protected route example
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"msg": f"Welcome, {current_user.username}"}


# Route to add a match to a user's favorite matches
@router.post("/favorite-match/{match_id}")
async def add_favorite_match(match_id: int, session: SessionDep, current_user: User = Depends(get_current_user), redis=Depends(get_redis)):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Check if the match is already in the user's favorites
    statement = select(UserMatchLink).where(
        (UserMatchLink.user_id == current_user.id) & (UserMatchLink.match_id == match_id)
    )
    favorite_link = session.exec(statement).first()

    if favorite_link:
        raise HTTPException(status_code=400, detail="Match already in favorites")

    # Add the match to user's favorites
    user_match_link = UserMatchLink(user_id=current_user.id, match_id=match_id)
    session.add(user_match_link)
    session.commit()

    # Update the cache with the new favorite match

    return {"msg": "Match added to favorites"}


# Route to remove a match from a user's favorite matches
@router.delete("/favorite-match/{match_id}")
async def remove_favorite_match(match_id: int, session: SessionDep, current_user: User = Depends(get_current_user), redis=Depends(get_redis)):
    # Find the match in the user's favorites
    statement = select(UserMatchLink).where(
        (UserMatchLink.user_id == current_user.id) & (UserMatchLink.match_id == match_id)
    )
    favorite_link = session.exec(statement).first()

    if not favorite_link:
        raise HTTPException(status_code=404, detail="Favorite match not found")

    # Remove the match from favorites
    session.delete(favorite_link)
    session.commit()

    # Update the cache by removing the match
    await remove_favorite_match(redis, current_user.id, match_id)

    return {"msg": "Match removed from favorites"}


# Route to list all favorite matches for the current user
@router.get("/favorite-matches")
async def get_favorite_matches(session: SessionDep, current_user: User = Depends(get_current_user), redis=Depends(get_redis)):
    # Check the cache for favorite matches first
    cached_favorite_matches = await get_cached_favorite_matches(redis, current_user.id)
    if cached_favorite_matches:
        return {"favorite_matches": cached_favorite_matches}

    # If not in cache, fetch from the database
    statement = select(Match).join(UserMatchLink).where(UserMatchLink.user_id == current_user.id)
    favorite_matches = session.exec(statement).all()

    # Cache the fetched favorite matches
    await add_favorite_match(redis, current_user.id, favorite_matches)

    return {"favorite_matches": favorite_matches}
