import React, { useEffect, useRef } from "react";
import { BOX_W, BOX_H, worldToScreen, screenToWorld, worldLenToPxX, worldLenToPxY, rgb } from "./coords.js";

export default function SimCanvas({ sim, send }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, BOX_W, BOX_H);

    if (!sim) return;

    ctx.fillStyle = "#1e1e1e";
    ctx.fillRect(0, 0, BOX_W, BOX_H);

    // Boundary box
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 3;
    ctx.strokeRect(1.5, 1.5, BOX_W - 3, BOX_H - 3);

    // Gravity wells
    for (const well of sim.wells) {
      const [sx, sy] = worldToScreen(well.x, well.y);
      ctx.beginPath();
      ctx.arc(sx, sy, 10, 0, 2 * Math.PI);
      ctx.fillStyle = "rgb(180,60,255)";
      ctx.fill();
      ctx.strokeStyle = "rgb(220,140,255)";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "rgb(220,180,255)";
      ctx.font = "13px monospace";
      ctx.fillText(`M=${Math.round(well.mass)}`, sx + 13, sy + 4);
    }

    // User-drawn walls
    ctx.lineWidth = 3;
    for (const w of sim.walls) {
      const [sx1, sy1] = worldToScreen(w.x1, w.y1);
      const [sx2, sy2] = worldToScreen(w.x2, w.y2);
      ctx.strokeStyle = "rgb(255,200,80)";
      ctx.beginPath();
      ctx.moveTo(sx1, sy1);
      ctx.lineTo(sx2, sy2);
      ctx.stroke();
      ctx.fillStyle = "rgb(255,200,80)";
      [[sx1, sy1], [sx2, sy2]].forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Wall preview while drawing
    if (sim.wall_drawing && sim.wall_start && canvas._lastMouse) {
      const [sx1, sy1] = worldToScreen(sim.wall_start[0], sim.wall_start[1]);
      const { x: mx, y: my } = canvas._lastMouse;
      ctx.strokeStyle = "rgb(180,140,50)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(sx1, sy1);
      ctx.lineTo(mx, my);
      ctx.stroke();
      ctx.fillStyle = "rgb(255,200,80)";
      ctx.beginPath();
      ctx.arc(sx1, sy1, 4, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Springs
    const byId = {};
    for (const b of sim.balls) byId[b.id] = b;
    for (const r of sim.rects) byId[r.id] = r;

    for (const sp of sim.springs) {
      const a = byId[sp.a], b = byId[sp.b];
      if (!a || !b) continue;
      const [sx1, sy1] = worldToScreen(a.x, a.y);
      const [sx2, sy2] = worldToScreen(b.x, b.y);
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      let strain = (d - sp.L0) / Math.max(sp.L0, 1e-8);
      strain = Math.max(-1, Math.min(1, strain));
      const col = strain >= 0
        ? `rgb(80, ${Math.round(80 + 175 * strain)}, 80)`
        : `rgb(${Math.round(80 + 175 * -strain)}, 80, 80)`;
      ctx.strokeStyle = col;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(sx1, sy1);
      ctx.lineTo(sx2, sy2);
      ctx.stroke();
    }

    // Balls
    for (const ball of sim.balls) {
      const [sx, sy] = worldToScreen(ball.x, ball.y);
      const rp = Math.max(1, worldLenToPxX(ball.radius));
      ctx.beginPath();
      ctx.arc(sx, sy, rp, 0, 2 * Math.PI);
      ctx.fillStyle = rgb(ball.colour);
      ctx.fill();
      if (ball.id === sim.selected_id) {
        ctx.strokeStyle = "rgb(80,255,80)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(sx, sy, rp + 4, 0, 2 * Math.PI);
        ctx.stroke();
      }
      if (ball.id === sim.spring_selected_id) {
        ctx.strokeStyle = "rgb(255,255,255)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(sx, sy, rp + 3, 0, 2 * Math.PI);
        ctx.stroke();
      }
    }

    // Rectangles
    for (const rect of sim.rects) {
      const [sx, sy] = worldToScreen(rect.x - rect.length / 2, rect.y + rect.width / 2);
      const lenX = Math.max(1, worldLenToPxX(rect.length));
      const lenY = Math.max(1, worldLenToPxY(rect.width));
      ctx.fillStyle = rgb(rect.colour);
      ctx.fillRect(sx, sy, lenX, lenY);
      if (rect.id === sim.selected_id) {
        ctx.strokeStyle = "rgb(80,255,80)";
        ctx.lineWidth = 2;
        ctx.strokeRect(sx - 3, sy - 3, lenX + 6, lenY + 6);
      }
      if (rect.id === sim.spring_selected_id) {
        ctx.strokeStyle = "rgb(255,255,255)";
        ctx.lineWidth = 2;
        ctx.strokeRect(sx - 3, sy - 3, lenX + 6, lenY + 6);
      }
    }

    // Spring preview line from spring_selected_obj to mouse
    if (sim.mode === "SPRING" && sim.spring_selected_id != null && canvas._lastMouse) {
      const obj = byId[sim.spring_selected_id];
      if (obj) {
        const [sx1, sy1] = worldToScreen(obj.x, obj.y);
        const { x: mx, y: my } = canvas._lastMouse;
        ctx.strokeStyle = "rgb(180,180,80)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(sx1, sy1);
        ctx.lineTo(mx, my);
        ctx.stroke();
      }
    }
  }, [sim]);

  function getMouseWorld(e) {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    // Scale by actual-rendered-size -> internal-resolution ratio so clicks
    // stay correct even if the canvas is ever displayed at a different
    // CSS size than its width/height attributes (e.g. responsive layouts).
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const sx = (e.clientX - rect.left) * scaleX;
    const sy = (e.clientY - rect.top) * scaleY;
    canvas._lastMouse = { x: sx, y: sy };
    return screenToWorld(sx, sy);
  }

  function handleMouseDown(e) {
    const [wx, wy] = getMouseWorld(e);
    send({ type: "canvas_click", x: wx, y: wy });
  }

  function handleMouseUp(e) {
    const [wx, wy] = getMouseWorld(e);
    send({ type: "canvas_mouseup", x: wx, y: wy });
  }

  function handleMouseMove(e) {
    getMouseWorld(e); // updates canvasRef._lastMouse for previews, drawn next tick
  }

  return (
    <canvas
      ref={canvasRef}
      width={BOX_W}
      height={BOX_H}
      className="sim-canvas"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseMove={handleMouseMove}
    />
  );
}
