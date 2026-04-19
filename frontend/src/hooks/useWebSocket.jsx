import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { WS_URL, WS_RECONNECT_MS } from '../utils/constants';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const [data, setData] = useState({
    pressure: {},
    predictions: {},
    alerts: [],
    classifications: {},
    flow_rates: {},
    flow_history: {},
    locations: [],
    timestamp: null,
    // Scenario extensions
    aarti_context: {},
    calendar_context: {},
    event_context: {},
    auspicious_context: {},
    procession_status: {},
    anomaly_data: {},
    counter_flow: {},
    cluster_data: {},
    toll_status: [],
    transit_status: {},
    zone_status: {},
  });
  
  const [isConnected, setIsConnected] = useState(false);
  
  const connect = useCallback(() => {
    console.log(`[WS] Connecting to ${WS_URL}`);
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('[WS] Connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'state_update') {
          setData(prev => ({
            ...prev,
            ...msg.data,
          }));
        } else if (msg.type === 'pong') {
          // Heartbeat response
        }
      } catch (err) {
        console.error('[WS] Error parsing message:', err);
      }
    };

    ws.onclose = () => {
      console.log(`[WS] Disconnected. Reconnecting in ${WS_RECONNECT_MS}ms...`);
      setIsConnected(false);
      setTimeout(connect, WS_RECONNECT_MS);
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
      ws.close();
    };

    return ws;
  }, []);

  useEffect(() => {
    const ws = connect();
    
    // Heartbeat to keep connection alive
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 15000);

    return () => {
      clearInterval(interval);
      ws.onclose = null; // Prevent auto-reconnect on unmount
      ws.close();
    };
  }, [connect]);

  // Make data available to all components
  return (
    <WebSocketContext.Provider value={{ ...data, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
