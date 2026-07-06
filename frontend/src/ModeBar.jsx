import React from "react";

const MODES = [
  { key: "BALL", label: "Ball", colour: "rgb(100,220,255)" },
  { key: "RECTANGLE", label: "Rect", colour: "rgb(100,100,255)" },
  { key: "WALL", label: "Wall", colour: "rgb(255,180,50)" },
  { key: "SPRING", label: "Spring", colour: "rgb(180,255,100)" },
  { key: "WELL", label: "Well", colour: "rgb(220,100,255)" },
];

export default function ModeBar({ sim, send }) {
  return (
    <div className="mode-bar">
      <div className="mode-buttons">
        {MODES.map((m) => (
          <button
            key={m.key}
            className={"mode-btn" + (sim.mode === m.key ? " mode-btn-active" : "")}
            style={{ borderColor: m.colour, color: sim.mode === m.key ? m.colour : "#999" }}
            onClick={() => send({ type: "set_mode", mode: m.key })}
          >
            {m.label}
          </button>
        ))}
      </div>
      <div className="mode-right">
        <button
          className={"pause-btn" + (sim.paused ? " pause-btn-active" : "")}
          onClick={() => send({ type: "toggle_pause" })}
        >
          {sim.paused ? "▶ Resume" : "⏸ Pause"}
        </button>
        <DeleteMenu sim={sim} send={send} />
      </div>
    </div>
  );
}

function DeleteMenu({ sim, send }) {
  const kindForMode = {
    BALL: "ball",
    RECTANGLE: "rect",
    WALL: "wall",
    SPRING: "spring",
    WELL: "well",
  }[sim.mode];

  if (!kindForMode) return null;

  return (
    <button
      className="delete-btn"
      title={`Delete last ${kindForMode}`}
      onClick={() => send({ type: "delete_last", kind: kindForMode })}
    >
      🗑 Delete last {kindForMode}
    </button>
  );
}
