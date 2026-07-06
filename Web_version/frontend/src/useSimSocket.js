import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

export function useSimSocket() {
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let socket;

    function connect() {
      socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => !cancelled && setConnected(true);
      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        setTimeout(connect, 1000); // auto-reconnect
      };
      socket.onerror = () => socket.close();
      socket.onmessage = (evt) => {
        if (cancelled) return;
        setState(JSON.parse(evt.data));
      };
    }

    connect();
    return () => {
      cancelled = true;
      socket && socket.close();
    };
  }, []);

  const send = useCallback((msg) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  return { state, connected, send };
}
