import asyncio
import socketio
import json
from src.config.redis import redis_connection

# Create Socket.IO server instance
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["http://127.0.0.1:5500"],  # Frontend origin
    logger=True,
    engineio_logger=True,
)

# In-memory mapping of Redis pubsub instances for matches
redis_subscribers = {}  # {channel: {"pubsub": pubsub_instance, "sids": set()}}

# Define event handlers for Socket.IO
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

    # Remove SID from all subscribed channels
    for channel, data in list(redis_subscribers.items()):
        data["sids"].discard(sid)
        # Cleanup if no SIDs are subscribed to the channel
        if not data["sids"]:
            await data["pubsub"].unsubscribe(channel)
            del redis_subscribers[channel]


@sio.on("subscribe")
async def subscribe_to_match(sid, data):
    match_id = data.get("match_id")
    if not match_id:
        await sio.emit("error", {"message": "Match ID is required"}, to=sid)
        return

    # Subscribe to Redis Pub/Sub for the match
    redis = await redis_connection()
    channel = f"match_update:{match_id}"

    if channel not in redis_subscribers:
        pubsub = redis.pubsub()
        # Sub scribe from here
        await pubsub.subscribe(channel)
        redis_subscribers[channel] = {"pubsub": pubsub, "sids": set()}

        async def listen_to_channel():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    update = json.loads(message["data"])
                    # Broadcast the update to all subscribed clients
                    for client_sid in redis_subscribers[channel]["sids"]:
                        await sio.emit("match_update", update, to=client_sid)

        # Run the listener in a background task
        sio.start_background_task(listen_to_channel)

    # Add the client SID to the set of subscribers for this channel
    redis_subscribers[channel]["sids"].add(sid)

    await sio.emit("subscribed", {"message": f"Subscribed to match {match_id}"}, to=sid)


@sio.on("unsubscribe")
async def unsubscribe_from_match(sid, data):
    match_id = data.get("match_id")
    if not match_id:
        await sio.emit("error", {"message": "Match ID is required"}, to=sid)
        return

    channel = f"match_update:{match_id}"
    if channel in redis_subscribers:
        # Remove SID from the channel
        redis_subscribers[channel]["sids"].discard(sid)
        # Cleanup if no SIDs are subscribed to the channel
        if not redis_subscribers[channel]["sids"]:
            pubsub = redis_subscribers[channel]["pubsub"]
            await pubsub.unsubscribe(channel)
            del redis_subscribers[channel]

    await sio.emit("unsubscribed", {"message": f"Unsubscribed from match {match_id}"}, to=sid)
