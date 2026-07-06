import React from "react";

const SPECS = [
  { key: "x", label: "x(t)", colour: "rgb(100,220,255)" },
  { key: "y", label: "y(t)", colour: "rgb(255,180,80)" },
  { key: "vx", label: "vx(t)", colour: "rgb(160,255,120)" },
  { key: "vy", label: "vy(t)", colour: "rgb(255,120,200)" },
];

const W = 260;
const H = 100;
const PAD = 10;

function SingleGraph({ history, spec }) {
  if (history.length < 2) {
    return (
      <svg width={W} height={H} className="graph-svg">
        <rect width={W} height={H} fill="rgba(0,0,0,0.4)" />
        <text x={4} y={14} fill="#ccc" fontSize="11" fontFamily="monospace">{spec.label}</text>
      </svg>
    );
  }

  const t0 = history[0].t;
  const t1 = history[history.length - 1].t;
  const tSpan = Math.max(t1 - t0, 1e-6);
  const vals = history.map((p) => p[spec.key]);
  const vMin = Math.min(...vals);
  const vMax = Math.max(...vals);
  const vRange = Math.max(vMax - vMin, 1e-6);

  const toX = (t) => PAD + ((t - t0) / tSpan) * (W - 2 * PAD);
  const toY = (v) => H - PAD - ((v - vMin) / vRange) * (H - 2 * PAD);

  const points = history.map((p) => `${toX(p.t)},${toY(p[spec.key])}`).join(" ");
  const cur = vals[vals.length - 1];

  return (
    <svg width={W} height={H} className="graph-svg">
      <rect width={W} height={H} fill="rgba(0,0,0,0.4)" />
      <polyline points={points} fill="none" stroke={spec.colour} strokeWidth={2} />
      <text x={4} y={12} fill={spec.colour} fontSize="11" fontFamily="monospace">{spec.label}</text>
      <text x={W - 4} y={12} fill="#ccc" fontSize="11" fontFamily="monospace" textAnchor="end">
        {cur >= 0 ? "+" : ""}{cur.toFixed(2)}
      </text>
    </svg>
  );
}

export default function Graphs({ history }) {
  return (
    <div className="graphs-panel">
      {SPECS.map((spec) => (
        <SingleGraph key={spec.key} history={history} spec={spec} />
      ))}
    </div>
  );
}
