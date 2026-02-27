"""
P2P File Share — Signaling Server
Relays WebRTC offer/answer/ICE between two peers in a room.
The actual file data travels directly between browsers (P2P).
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("p2p-fileshare")

app = FastAPI(title="P2P File Share Signaling Server")

# rooms[room_id] = [websocket, ...]  (max 2 peers per room)
rooms: dict[str, list[WebSocket]] = {}


@app.websocket("/ws/{room_id}")
async def signaling(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = []

    if len(rooms[room_id]) >= 2:
        await websocket.send_text(json.dumps({"type": "error", "message": "Room is full (max 2 peers)."}))
        await websocket.close()
        return

    rooms[room_id].append(websocket)
    is_initiator = len(rooms[room_id]) == 1

    log.info(f"Peer joined room '{room_id}' ({'initiator' if is_initiator else 'receiver'}). Room size: {len(rooms[room_id])}")

    # Tell this peer its role
    await websocket.send_text(json.dumps({
        "type": "role",
        "role": "initiator" if is_initiator else "receiver"
    }))

    # When the second peer joins, tell the initiator to start the WebRTC handshake
    if not is_initiator:
        initiator = rooms[room_id][0]
        await initiator.send_text(json.dumps({"type": "peer_joined"}))

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            # Relay signaling messages (offer, answer, ice-candidate) to the other peer
            others = [p for p in rooms[room_id] if p is not websocket]
            for peer in others:
                await peer.send_text(raw)

    except WebSocketDisconnect:
        if room_id in rooms:
            rooms[room_id] = [p for p in rooms[room_id] if p is not websocket]
            if not rooms[room_id]:
                del rooms[room_id]
                log.info(f"Room '{room_id}' deleted (empty).")
            else:
                for peer in rooms[room_id]:
                    await peer.send_text(json.dumps({"type": "peer_disconnected"}))
        log.info(f"Peer left room '{room_id}'.")


# Serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
