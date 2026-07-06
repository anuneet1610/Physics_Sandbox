import React, { useState, useEffect } from "react";

const EDITABLE = new Set(["mass", "radius", "length", "width", "x", "y", "vx", "vy"]);

function EditableCell({ obj, field, value, send }) {
  const [text, setText] = useState(value);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!editing) setText(value);
  }, [value, editing]);

  function commit() {
    setEditing(false);
    if (text === "" || isNaN(parseFloat(text))) return;
    send({ type: "update_field", obj_id: obj.id, field, value: parseFloat(text) });
  }

  return (
    <input
      className="info-cell editable"
      value={editing ? text : value}
      onFocus={() => setEditing(true)}
      onChange={(e) => setText(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.target.blur();
        if (e.key === "Escape") { setEditing(false); setText(value); }
      }}
    />
  );
}

function ReadonlyCell({ value }) {
  return <input className="info-cell readonly" value={value} readOnly tabIndex={-1} />;
}

export default function InfoPanel({ sim, send }) {
  const obj = [...sim.balls, ...sim.rects].find((o) => o.id === sim.selected_id);

  if (!obj) {
    return (
      <div className="info-panel info-panel-empty">
        Select an object from the side panel to see its info
      </div>
    );
  }

  const isRect = obj.kind === "rect";
  const mass = obj.mass;
  const ax = mass ? obj.fx / mass : 0;
  const ay = mass ? obj.fy / mass : 0;
  const px = mass * obj.vx;
  const py = mass * obj.vy;
  const ke = 0.5 * mass * (obj.vx * obj.vx + obj.vy * obj.vy);
  const pe = mass * sim.g * obj.y;

  const fmt = (v, d = 4) => (typeof v === "number" ? v.toFixed(d) : v);

  const sizeRow = isRect
    ? { label: "Length / Width", cells: [["length", obj.length], ["width", obj.width]] }
    : { label: "Radius", cells: [["radius", obj.radius]] };

  const rows = [
    { label: "Mass", cells: [["mass", mass]] },
    sizeRow,
    { label: "Position", cells: [["x", obj.x], ["y", obj.y]] },
    { label: "Velocity", cells: [["vx", obj.vx], ["vy", obj.vy]] },
    { label: "Acceleration", cells: [[null, ax], [null, ay]] },
    { label: "Momentum", cells: [[null, px], [null, py]] },
    { label: "KE", cells: [[null, ke]] },
    { label: "PE", cells: [[null, pe]] },
  ];

  const title = isRect
    ? `Rectangle #${sim.rects.findIndex((r) => r.id === obj.id) + 1}`
    : `Ball #${sim.balls.findIndex((b) => b.id === obj.id) + 1}`;

  return (
    <div className="info-panel">
      <div className="info-title" style={{ color: `rgb(${obj.colour.join(",")})` }}>{title}</div>
      {rows.map(({ label, cells }) => (
        <div className="info-row" key={label}>
          <span className="info-label">{label}</span>
          <div className="info-values">
            {cells.map(([field, value], i) =>
              field && EDITABLE.has(field) ? (
                <EditableCell key={i} obj={obj} field={field} value={fmt(value)} send={send} />
              ) : (
                <ReadonlyCell key={i} value={fmt(value)} />
              )
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
