import React from "react";
import { rgb } from "./coords.js";

export default function ObjectPanel({ sim, send }) {
  const items = [
    ...sim.balls.map((b, i) => ({ obj: b, label: `B${i + 1}`, shape: "circle" })),
    ...sim.rects.map((r, i) => ({ obj: r, label: `R${i + 1}`, shape: "square" })),
  ];

  const linkedIds = new Set();
  if (sim.spring_selected_id != null) {
    for (const sp of sim.springs) {
      if (sp.a === sim.spring_selected_id) linkedIds.add(sp.b);
      if (sp.b === sim.spring_selected_id) linkedIds.add(sp.a);
    }
  }

  return (
    <div className="object-panel">
      <div className="object-panel-title">Objects</div>
      {items.map(({ obj, label, shape }) => {
        const isSpringSel = obj.id === sim.spring_selected_id;
        const isInfoSel = obj.id === sim.selected_id;
        const isLinked = linkedIds.has(obj.id);
        let rowClass = "object-row";
        if (isSpringSel) rowClass += " row-spring-selected";
        else if (isInfoSel) rowClass += " row-info-selected";
        else if (isLinked) rowClass += " row-linked";

        return (
          <div
            key={obj.id}
            className={rowClass}
            onClick={() => send({ type: "panel_click", obj_id: obj.id })}
          >
            <span
              className={shape === "circle" ? "swatch-circle" : "swatch-square"}
              style={{ background: rgb(obj.colour) }}
            />
            <span className="object-label">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
