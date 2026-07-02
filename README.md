# 2D Physics Sandbox

A 2D physics simulation built from scratch in Python using **Pygame**. You can drop balls and rectangles into a bounded world, draw walls, connect objects with springs, place gravity wells, and watch everything collide and move in real time. There's also a live info panel and kinematics graphs for whatever object you select.

**No physics engine or physics library is used anywhere in this project.** Every bit of physics — gravity, forces, integration, collision detection, collision response, spring dynamics, gravitational attraction — is written from scratch using plain Python and basic vector math. Pygame is only used for rendering, windowing, and input handling; it does not provide any physics.

## What it does

- Spawn **balls** and **rectangles** with random velocities, sizes, and colours
- Draw **walls** anywhere in the world by clicking and dragging
- Connect objects with **springs** (with damping) by wiring them together in the side panel
- Place **gravity wells** that pull nearby objects toward them, following the laws of gravity
- Select any object to see a live, **editable info panel** (mass, position, velocity, size, etc. can be typed in directly)
- Watch **live graphs** of x(t), y(t), vx(t), and vy(t) for the selected object
- Adjust **gravity** and **restitution (bounciness)** on the fly using sliders
- **Pause** the simulation at any time

## Controls

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


## Screenshots

### Description of UI
It shows one ball and one rectangle in the window. Currently the ball is selected, and its info is displayed in the bottom-most panel. The live graphs of its x-axis position, y-axis position, x-axis velocity and y-axis velocity are also displayed in the right. There is a panel just to the right of the window, which lists all the objects present, and you can select them from here. There are two sliders, one for adjusting the acceleration due to gravity (g), and other one to adjust the coefficient of restitution (e: it is to adjust the energy lost in a collision). There are 5 modes:
1. Wall Mode [W]: Toggle this mode to draw a wall anywhere in the world.
2. Spring Mode [S]: Toggle this mode to attach a spring between any two objects. First press [S], then select the two objects one by one from the Objects list.
3. Ball Mode [B]: Toggle this mode to draw a ball by clicking anywhere in the world, initiated with random velocity (you can edit it later using info panel).
4. Rectangle Mode [R]: Toggle this mode to draw a rectangle by clicking anywhere in the world, initiated with random dimensions and velocity (you can edit it later using info panel).
5. Gravity Well [G]: Toggle this mode to add a fixed Gravity Well by clicking anywhere in the world, with a fixed mass of 1000 kg.

You can pause the scene by pressing [P], and make any kind of changes you want.

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
```

### `main.py`
The entry point. Sets up the initial walls, balls, and rectangles, opens the Pygame window, and runs the main loop. Each frame it:
1. Handles keyboard/mouse input (mode switching, spawning objects, dragging sliders, editing fields)
2. Steps the physics: clears forces → applies springs and gravity wells → integrates motion → resolves wall collisions → resolves ball/rectangle collisions → clamps everything inside the world boundary
3. Records the selected object's position/velocity history (for the graphs)
4. Draws everything to the screen

### `bodies.py`
Defines `RigidBody`, the base class every physics object inherits from. It stores position, velocity, mass, and accumulated force, and implements basic semi-implicit Euler integration (`F = ma`, update velocity then position). `Ball` and `Rectangle` extend it with their own shape data and their own `check_collision` methods (ball-ball, rectangle-rectangle, and rectangle-ball), all handled with basic impulse-based collision resolution.

### `collisions.py`
Handles collisions between objects and walls. Includes both a "static" check (object already overlapping a wall) and a "swept" check (object moving fast enough to tunnel through a wall in a single frame — caught by checking which side of the wall the object was on last frame vs. this frame). Also contains the logic that keeps every object inside the outer world boundary.

### `wall.py`
A minimal `Wall` class: just two endpoints, with the segment's length, tangent direction, and normal direction precomputed once.

### `spring.py`
A `Spring` connects two bodies and applies a force proportional to how far the spring is stretched or compressed from its rest length, plus a damping term based on relative velocity along the spring.

### `gravity_well.py`
A `Gravity_Well` pulls balls and rectangles toward it using an inverse-square law (`F = G * m1 * m2 / r^2`), similar to Newtonian gravity, in addition to the normal downward gravity from `state.g`.

### `state.py`
Holds shared, mutable values used across the whole project — current gravity, restitution, current interaction mode (BALL/WALL/SPRING/etc.), which object is selected, pause state, world size, and the rolling history of the selected object's motion (used for the graphs).

### `config.py`
Just layout constants — window size, where the simulation box is drawn on screen, and where the graph panel sits.

### `coords.py`
Two small functions that convert between "world" coordinates (metres, y-up, used by the physics) and "screen" coordinates (pixels, y-down, used by Pygame) so the two systems never get mixed up.

### `ui.py`
Everything visual that isn't the simulation itself: the gravity/restitution sliders, the mode indicator, the pause indicator, the object list panel (used for spring wiring and selection), the editable info panel for the selected object, and the four kinematics graphs (x, y, vx, vy over time).

## Requirements

- Python 3
- Pygame (`pip install pygame`)

## Running it

```bash
python main.py
```
