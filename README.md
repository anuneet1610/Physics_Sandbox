# Physics Sandbox — React + FastAPI

A port of the original pygame physics sandbox to a web app:
- **backend/** — FastAPI server. Owns the simulation (balls, rectangles, walls,
  springs, gravity wells) and runs the physics loop server-side, streaming
  state to the browser over a WebSocket at 60Hz.
- **frontend/** — React (Vite) app. Renders the world on a `<canvas>` and
  the side panel / sliders / info panel / kinematics graphs in HTML/SVG.

## Run the backend
```
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run the frontend
```
cd frontend
npm install
cp .env.example .env   # points at ws://localhost:8000/ws by default
npm run dev
```
Then open http://localhost:5173.

## Architecture notes
- All physics math (integration, collisions, springs, gravity wells) was
  ported near-verbatim from the original `bodies.py` / `collisions.py` /
  `spring.py` / `gravity_well.py` / `wall.py` into `backend/physics/`.
  The old `state.py` module-level globals are now instance attributes on
  `SimulationState` (`backend/physics/simulation.py`), so each connection
  could in principle get its own independent sim if you want multi-room
  support later — right now everyone shares one global `sim`.
- The old pygame event loop (mouse clicks placing objects, keyboard mode
  switches, dragging sliders, editing the info panel) is now a set of
  JSON "commands" sent over the WebSocket (`main.py`'s `handle_command`),
  mirroring each of the old `if event.type == ...` branches.
- The Z+key "delete last X" shortcuts became a "Delete last <type>" button
  that's aware of the current mode, since browsers don't expose the same
  raw-keyboard modifier ergonomics as pygame.
- Frontend editable fields (mass/radius/x/y/vx/vy etc.) are plain
  `<input>`s that commit on blur/Enter, replacing the old manual
  keystroke-buffer editing in `ui.py`.

## Deploying: Render (backend) + Vercel (frontend)

Vercel's serverless functions can't hold a long-lived WebSocket open, which
is what the sim needs, so the FastAPI backend goes on Render (a normal
persistent process) and only the static React build goes on Vercel.

### 1. Backend on Render
1. Push this repo to GitHub.
2. In Render: **New > Blueprint**, point it at the repo — it'll pick up
   `render.yaml` at the root automatically (root dir `backend`, start
   command `uvicorn main:app --host 0.0.0.0 --port $PORT`).
   - Or set it up manually as a **Web Service**: root dir `backend`,
     build command `pip install -r requirements.txt`, start command
     `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Once deployed you'll get a URL like `https://physics-sandbox-backend.onrender.com`.
   Test it: `https://<that-url>/health` should return `{"status":"ok"}`.
4. Leave `ALLOWED_ORIGINS=*` for now — you'll lock it down in step 3 below.

Note: Render's free tier spins the service down after inactivity, so the
first WebSocket connect after idle time will be slow (~30-60s cold start)
and `useSimSocket`'s auto-reconnect will just keep retrying until it's up.

### 2. Frontend on Vercel
1. In Vercel: **New Project**, import the same repo, set **root directory**
   to `frontend` (it'll auto-detect Vite via `vercel.json`).
2. Add an environment variable:
   `VITE_WS_URL = wss://physics-sandbox-backend.onrender.com/ws`
   (note **wss://**, not ws://, since Render serves over HTTPS — and no
   trailing slash after `/ws`).
3. Deploy. You'll get a URL like `https://physics-sandbox.vercel.app`.

### 3. Lock down CORS/origin checks
Back in Render, set the backend's `ALLOWED_ORIGINS` env var to your actual
Vercel URL (comma-separate multiple if you have a preview + prod domain):
```
ALLOWED_ORIGINS=https://physics-sandbox.vercel.app
```
Redeploy the backend for it to take effect. This is enforced both via
`CORSMiddleware` (for the `/health` HTTP route) and an explicit `Origin`
header check in the `/ws` WebSocket handler (browsers don't apply normal
CORS rules to WebSocket upgrades, so the middleware alone isn't enough).
