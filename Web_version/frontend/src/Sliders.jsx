import React from "react";

// Vertical range inputs, styled to stand in for the old pygame drag-handles.
export default function Sliders({ g, e, send }) {
  return (
    <div className="sliders">
      <div className="slider-col">
        <div className="slider-label">g = {g.toFixed(2)}</div>
        <input
          type="range"
          min={-20}
          max={20}
          step={0.1}
          value={g}
          orient="vertical"
          className="vertical-slider"
          onChange={(ev) => send({ type: "set_g", value: parseFloat(ev.target.value) })}
        />
      </div>
      <div className="slider-col">
        <div className="slider-label">e = {e.toFixed(2)}</div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={e}
          orient="vertical"
          className="vertical-slider slider-e"
          onChange={(ev) => send({ type: "set_e", value: parseFloat(ev.target.value) })}
        />
      </div>
    </div>
  );
}
