# 2D Physics Sandbox

A 2D physics simulation built from scratch — no physics engine or physics library used anywhere. Every bit of physics — gravity, forces, integration, collision detection, collision response, spring dynamics, gravitational attraction — is written using plain math and vectors. You can drop balls and rectangles into a bounded world, draw walls, connect objects with springs, place gravity wells, and watch everything collide and move in real time. There's also a live info panel and kinematics graphs for whatever object you select.

This repo contains two implementations:

- **`pygame_version/`** — the original standalone desktop app, built in Python with Pygame. Pygame is only used for rendering, windowing, and input handling; it provides no physics.
- **`web_version/`** — a port of the same simulation to a web app, with a **FastAPI** backend that owns and runs the physics loop server-side (streaming state to the browser over a WebSocket at 60Hz) and a **React (Vite)** frontend that renders the world on a `<canvas>` with the side panel / sliders / info panel / kinematics graphs in HTML/SVG.

## What it does

- Spawn **balls** and **rectangles** with random velocities, sizes, and colours
- Draw **walls** anywhere in the world by clicking and dragging
- Connect objects with **springs** (with damping) by wiring them together in the side panel
- Place **gravity wells** that pull nearby objects toward them, following the laws of gravity
- Select any object to see a live, **editable info panel** (mass, position, velocity, size, etc. can be typed in directly)
- Watch **live graphs** of x(t), y(t), vx(t), and vy(t) for the selected object
- Adjust **gravity** and **restitution (bounciness)** on the fly using sliders
- **Pause** the simulation at any time

## Controls (Pygame version)

| Key | Action |
|---|---|
| `B` | Ball mode (click in the world to spawn a ball) |
| `R` | Rectangle mode |
| `W` | Wall mode (click and drag to draw a wall) |
| `S` | Spring mode (click two objects to link/unlink a spring) |
| `G` | Gravity well mode (click to place a well) |
| `P` | Pause / resume |
| `Z` + `B`/`R`/`W`/`S`/`G` | Delete the last object of that type |
| Click an object in the side panel | Select it and show its info panel + graphs |
| Click a yellow value in the info panel | Edit that field directly (type a number, `Enter` to confirm, `Esc` to cancel) |

In the web version, the same interactions (mode switching, spawning, dragging sliders, deleting last object, editing fields) are driven by on-screen buttons and plain `<input>` elements that commit on blur/Enter, since browsers don't expose the same raw-keyboard modifier ergonomics as Pygame. The Z+key "delete last X" shortcut becomes a "Delete last <type>" button aware of the current mode.

## Modes

1. **Wall Mode [W]**: Draw a wall anywhere in the world.
2. **Spring Mode [S]**: Attach a spring between any two objects. First toggle the mode, then select the two objects one by one from the Objects list.
3. **Ball Mode [B]**: Draw a ball by clicking anywhere in the world, initiated with random velocity (editable later via info panel).
4. **Rectangle Mode [R]**: Draw a rectangle by clicking anywhere in the world, initiated with random dimensions and velocity (editable later via info panel).
5. **Gravity Well [G]**: Add a fixed Gravity Well by clicking anywhere in the world, with a fixed mass of 1000 kg.

You can pause the scene with [P] (or the pause button in the web version), and make any changes you want while paused.

## Screenshots (Screenshots of Pygame UI. Almost same UI of Web Version)

### Description of UI
It shows one ball and one rectangle in the window. Currently the ball is selected, and its info is displayed in the bottom-most panel. The live graphs of its x-axis position, y-axis position, x-axis velocity and y-axis velocity are also displayed on the right. There is a panel just to the right of the window, which lists all the objects present, and you can select them from here. There are two sliders, one for adjusting the acceleration due to gravity (g), and another to adjust the coefficient of restitution (e: energy lost in a collision).

<img width="900" height="800" alt="SS_1" src="https://github.com/user-attachments/assets/9f74fc31-439c-4d9e-a5c4-181023460c26" />

### Added Objects with Springs
Two new rectangles and four new balls are added. There is a rectangle-rectangle, rectangle-ball and ball-ball pair connected with springs.

<img width="900" height="800" alt="SS_2" src="https://github.com/user-attachments/assets/88ceb642-37ec-4d3d-8460-aa7f5973ca58" />

### Added Walls
New walls are added

<img width="900" height="800" alt="SS_3" src="https://github.com/user-attachments/assets/93072272-b149-4079-a378-5ff941639cd1" />

### Added Gravity Well
A fixed Gravity Well is added of mass 1000 kg, and it is applying gravitational forces on each object

<img width="900" height="800" alt="SS_4" src="https://github.com/user-attachments/assets/9a3bcbf7-bc60-4c47-aaa5-5634b3b43960" />

### Edit Mass using Bottom Panel
Mass of the rectangle is changed using the bottom panel.

<img width="900" height="800" alt="SS_5" src="https://github.com/user-attachments/assets/cbe33361-8c2b-498f-bb77-f0cffb7aa92d" />

## File structure

```
pygame_version/
    main.py          Entry point: game loop, event handling, physics step order, rendering
    ui.py            All UI drawing and interaction — sliders, info panel, spring panel, graphs
    bodies.py        RigidBody base class, plus Ball and Rectangle (physics + collision response)
    collisions.py    Ball/rectangle vs wall collision detection and resolution, world boundary clamping
    wall.py          Simple Wall class (a line segment with precomputed normal/tangent)
    spring.py        Spring class — spring-damper force between two objects
    gravity_well.py  Gravity_Well class — applies an inverse-square attractive force to nearby objects
    state.py         Shared mutable simulation state (gravity, restitution, mode, selection, timers, etc.)
    config.py        Screen/window layout constants (panel positions, sizes)
    coords.py        Converts between world coordinates (metres) and screen coordinates (pixels)

web_version/
    backend/
        main.py               FastAPI app: WebSocket endpoint, command dispatch (handle_command),
                               health check route, CORS/origin setup
        requirements.txt      Backend Python dependencies
        physics/
            simulation.py     SimulationState — instance-based version of the old state.py globals
            bodies.py         RigidBody, Ball, Rectangle — ported near-verbatim from pygame_version
            collisions.py     Wall collision detection/resolution, world boundary clamping
            wall.py           Wall class
            spring.py         Spring class
            gravity_well.py   Gravity_Well class
        render.yaml           Render deployment blueprint (root dir, start command)
    frontend/
        package.json
        vite.config.js
        .env.example          Points at ws://localhost:8000/ws by default
        vercel.json            Vercel build config (auto-detected Vite root)
        src/
            useSimSocket.js   WebSocket hook: connects, sends commands, auto-reconnects on drop
            canvas/           Canvas rendering of the world (balls, rectangles, walls, springs, wells)
            panels/           Side object-list panel, editable info panel, mode controls
            graphs/           Kinematics graphs (x, y, vx, vy over time), SVG-based
            App.jsx           Top-level layout wiring canvas + panels + graphs together
```

### `pygame_version/main.py`
The entry point. Sets up the initial walls, balls, and rectangles, opens the Pygame window, and runs the main loop. Each frame it:
1. Handles keyboard/mouse input (mode switching, spawning objects, dragging sliders, editing fields)
2. Steps the physics: clears forces → applies springs and gravity wells → integrates motion → resolves wall collisions → resolves ball/rectangle collisions → clamps everything inside the world boundary
3. Records the selected object's position/velocity history (for the graphs)
4. Draws everything to the screen

### `pygame_version/bodies.py`
Defines `RigidBody`, the base class every physics object inherits from. It stores position, velocity, mass, and accumulated force, and implements basic semi-implicit Euler integration (`F = ma`, update velocity then position). `Ball` and `Rectangle` extend it with their own shape data and their own `check_collision` methods (ball-ball, rectangle-rectangle, and rectangle-ball), all handled with basic impulse-based collision resolution.

### `pygame_version/collisions.py`
Handles collisions between objects and walls. Includes both a "static" check (object already overlapping a wall) and a "swept" check (object moving fast enough to tunnel through a wall in a single frame — caught by checking which side of the wall the object was on last frame vs. this frame). Also contains the logic that keeps every object inside the outer world boundary.

### `pygame_version/wall.py`
A minimal `Wall` class: just two endpoints, with the segment's length, tangent direction, and normal direction precomputed once.

### `pygame_version/spring.py`
A `Spring` connects two bodies and applies a force proportional to how far the spring is stretched or compressed from its rest length, plus a damping term based on relative velocity along the spring.

### `pygame_version/gravity_well.py`
A `Gravity_Well` pulls balls and rectangles toward it using an inverse-square law (`F = G * m1 * m2 / r^2`), similar to Newtonian gravity, in addition to the normal downward gravity from `state.g`.

### `pygame_version/state.py`
Holds shared, mutable values used across the whole project — current gravity, restitution, current interaction mode (BALL/WALL/SPRING/etc.), which object is selected, pause state, world size, and the rolling history of the selected object's motion (used for the graphs).

### `pygame_version/config.py`
Just layout constants — window size, where the simulation box is drawn on screen, and where the graph panel sits.

### `pygame_version/coords.py`
Two small functions that convert between "world" coordinates (metres, y-up, used by the physics) and "screen" coordinates (pixels, y-down, used by Pygame) so the two systems never get mixed up.

### `pygame_version/ui.py`
Everything visual that isn't the simulation itself: the gravity/restitution sliders, the mode indicator, the pause indicator, the object list panel (used for spring wiring and selection), the editable info panel for the selected object, and the four kinematics graphs (x, y, vx, vy over time).

### `web_version/backend/`
FastAPI server. Owns the simulation (balls, rectangles, walls, springs, gravity wells) and runs the physics loop server-side, streaming state to the browser over a WebSocket at 60Hz. All physics math (integration, collisions, springs, gravity wells) was ported near-verbatim from the pygame version's `bodies.py` / `collisions.py` / `spring.py` / `gravity_well.py` / `wall.py` into `backend/physics/`. The old `state.py` module-level globals are now instance attributes on `SimulationState` (`backend/physics/simulation.py`), so each connection could in principle get its own independent sim if multi-room support is added later — right now everyone shares one global `sim`. The old pygame event loop (mouse clicks placing objects, keyboard mode switches, dragging sliders, editing the info panel) is now a set of JSON "commands" sent over the WebSocket (`main.py`'s `handle_command`), mirroring each of the old `if event.type == ...` branches.

### `web_version/frontend/`
React (Vite) app. Renders the world on a `<canvas>` and the side panel / sliders / info panel / kinematics graphs in HTML/SVG. Editable fields (mass/radius/x/y/vx/vy etc.) are plain `<input>`s that commit on blur/Enter, replacing the old manual keystroke-buffer editing in `ui.py`.

## Requirements

**Pygame version:**
- Python 3
- Pygame (`pip install pygame`)

**Web version:**
- Python 3, Node.js/npm

## Running it

### Pygame version
```bash
cd pygame_version
python main.py
```

### Web version — backend
```bash
cd web_version/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Web version — frontend
```bash
cd web_version/frontend
npm install
cp .env.example .env   # points at ws://localhost:8000/ws by default
npm run dev
```
Then open http://localhost:5173.

## Deploying the web version: Render (backend) + Vercel (frontend)

Vercel's serverless functions can't hold a long-lived WebSocket open, which is what the sim needs, so the FastAPI backend goes on Render (a normal persistent process) and only the static React build goes on Vercel.

### 1. Backend on Render
1. Push this repo to GitHub.
2. In Render: **New > Blueprint**, point it at the repo — it'll pick up `render.yaml` at the root automatically (root dir `web_version/backend`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`).
   - Or set it up manually as a **Web Service**: root dir `web_version/backend`, build command `pip install -r requirements.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Once deployed you'll get a URL like `https://physics-sandbox-backend.onrender.com`. Test it: `https://<that-url>/health` should return `{"status":"ok"}`.
4. Leave `ALLOWED_ORIGINS=*` for now — you'll lock it down in step 3 below.

Note: Render's free tier spins the service down after inactivity, so the first WebSocket connect after idle time will be slow (~30-60s cold start) and `useSimSocket`'s auto-reconnect will just keep retrying until it's up.

### 2. Frontend on Vercel
1. In Vercel: **New Project**, import the same repo, set **root directory** to `web_version/frontend` (it'll auto-detect Vite via `vercel.json`).
2. Add an environment variable:
   `VITE_WS_URL = wss://physics-sandbox-backend.onrender.com/ws`
   (note **wss://**, not ws://, since Render serves over HTTPS — and no trailing slash after `/ws`).
3. Deploy. You'll get a URL like `https://physics-sandbox.vercel.app`.

### 3. Lock down CORS/origin checks
Back in Render, set the backend's `ALLOWED_ORIGINS` env var to your actual Vercel URL (comma-separate multiple if you have a preview + prod domain):
```
ALLOWED_ORIGINS=https://physics-sandbox.vercel.app
```
Redeploy the backend for it to take effect. This is enforced both via `CORSMiddleware` (for the `/health` HTTP route) and an explicit `Origin` header check in the `/ws` WebSocket handler (browsers don't apply normal CORS rules to WebSocket upgrades, so the middleware alone isn't enough).
