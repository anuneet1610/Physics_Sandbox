import asyncio
import json
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from physics.simulation import SimulationState

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("physics-sandbox")

app = FastAPI(title="Physics Sandbox API")

# Comma-separated list, e.g. "https://your-app.vercel.app,http://localhost:5173"
# Falls back to "*" for local dev convenience.
_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = ["*"] if _origins_env.strip() == "*" else [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared simulation "room". For multi-room support, key a dict of
# SimulationState by room id and create one per websocket connection group.
sim = SimulationState()

TICK_HZ = 60
TICK_INTERVAL = 1 / TICK_HZ


@app.get("/health")
def health():
    return {"status": "ok"}


def handle_command(msg: dict):
    """Mirrors the old pygame event-handling branches in main.py."""
    mtype = msg.get("type")

    if mtype == "set_mode":
        sim.set_mode(msg.get("mode"))
    elif mtype == "toggle_pause":
        sim.toggle_pause()
    elif mtype == "set_g":
        sim.set_g(msg.get("value", sim.g))
    elif mtype == "set_e":
        sim.set_e(msg.get("value", sim.e))

    elif mtype == "canvas_click":
        wx, wy = msg["x"], msg["y"]
        mode = sim.mode
        if mode == "WELL":
            sim.add_well_at(wx, wy)
        elif mode == "BALL":
            sim.add_ball_at(wx, wy)
        elif mode == "WALL":
            sim.start_wall(wx, wy)
        elif mode == "RECTANGLE":
            sim.add_rect_at(wx, wy)

    elif mtype == "canvas_mouseup":
        wx, wy = msg["x"], msg["y"]
        sim.end_wall(wx, wy)

    elif mtype == "wall_preview":
        sim.wall_preview_end = (msg.get("x"), msg.get("y")) if sim.wall_drawing else None

    elif mtype == "panel_click":
        sim.select_object(msg.get("obj_id"))

    elif mtype == "delete_last":
        sim.delete_last(msg.get("kind"))

    elif mtype == "update_field":
        sim.update_field(msg.get("obj_id"), msg.get("field"), msg.get("value"))

    else:
        log.warning("Unknown command type: %s", mtype)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    origin = ws.headers.get("origin")
    if allowed_origins != ["*"] and origin not in allowed_origins:
        log.warning("Rejected WebSocket from disallowed origin: %s", origin)
        await ws.close(code=4403)
        return

    await ws.accept()

    async def receive_loop():
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                    handle_command(msg)
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    log.warning("Bad command %r: %s", raw, exc)
        except WebSocketDisconnect:
            pass

    async def send_loop():
        try:
            while True:
                sim.step()
                await ws.send_json(sim.to_state_dict())
                await asyncio.sleep(TICK_INTERVAL)
        except WebSocketDisconnect:
            pass

    receiver = asyncio.create_task(receive_loop())
    sender = asyncio.create_task(send_loop())
    try:
        await asyncio.gather(receiver, sender)
    except WebSocketDisconnect:
        pass
    finally:
        receiver.cancel()
        sender.cancel()
