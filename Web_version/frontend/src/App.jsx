import React from "react";
import { useSimSocket } from "./useSimSocket.js";
import SimCanvas from "./SimCanvas.jsx";
import ObjectPanel from "./ObjectPanel.jsx";
import Sliders from "./Sliders.jsx";
import InfoPanel from "./InfoPanel.jsx";
import Graphs from "./Graphs.jsx";
import ModeBar from "./ModeBar.jsx";

export default function App() {
  const { state: sim, connected, send } = useSimSocket();

  return (
    <div className="app">
      <h1 className="app-title">Physics Sandbox</h1>
      {!connected && <div className="connection-banner">Connecting to simulation server…</div>}
      {sim && (
        <>
          <ModeBar sim={sim} send={send} />
          <div className="main-row">
            <SimCanvas sim={sim} send={send} />
            <ObjectPanel sim={sim} send={send} />
            <Sliders g={sim.g} e={sim.e} send={send} />
            <Graphs history={sim.position_history} />
          </div>
          <InfoPanel sim={sim} send={send} />
        </>
      )}
    </div>
  );
}

