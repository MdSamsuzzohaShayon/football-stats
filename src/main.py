from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.
import socketio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from src.config.database import create_db_and_tables
from src.config.redis import redis_conn
from src.routers.team import router as team_router
from src.routers.player import router as player_router
from src.routers.match import router as match_router
from src.routers.auth import router as auth_router
from src.sockets import sio  # Import the `sio` instance from `sockets.py`


@asynccontextmanager
async def lifespan(app: FastAPI):

    create_db_and_tables()
    # Clear Redis database
    await redis_conn.flushdb()  # Clears all data in the Redis DB

    await FastAPILimiter.init(redis_conn)
    yield
    print("shutting down")


app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Integrate Socket.IO with FastAPI
socketio_app = socketio.ASGIApp(sio, app)

@app.get('/api')
def home():
    return {"message": "Home of the contract!"}


# Routers
app.include_router(team_router, prefix="/api/teams", tags=["Team"])
app.include_router(match_router, prefix="/api/matches", tags=["Match"])
app.include_router(player_router, prefix="/api/players", tags=["Player"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(socketio_app, host="127.0.0.1", port=8000, log_level="info")
