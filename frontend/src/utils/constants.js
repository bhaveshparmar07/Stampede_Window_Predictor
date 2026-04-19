// API and WebSocket URLs
// Default matches README + stream_data.py (uvicorn --port 8080)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
export const WS_URL = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/dashboard';
export const WS_RECONNECT_MS = 3000;

// Config
export const ALERT_SLA_SEC = 90;

export const PRESSURE_THRESHOLDS = {
  safe: { min: 0, max: 40, color: '#22c55e', label: 'Safe' },
  watch: { min: 40, max: 70, color: '#eab308', label: 'Watch' },
  critical: { min: 70, max: 100, color: '#ef4444', label: 'Critical' },
};

export const AGENCIES = {
  police: { label: 'District Police', action: 'Deploy officers to choke point' },
  temple: { label: 'Temple Trust', action: 'Activate darshan hold at inner sanctum gate' },
  transport: { label: 'GSRTC Transport Control', action: 'Hold all buses at 3 km holding zone' },
};

// Default seed locations. The system auto-discovers locations, 
// so this is mostly the default coordinates for the map.
export const LOCATION_COORDS = {
  Ambaji: { lat: 24.3338, lng: 72.8522 },
  Dwarka: { lat: 22.2442, lng: 68.9685 },
  Somnath: { lat: 20.8880, lng: 70.4012 },
  Pavagadh: { lat: 22.4693, lng: 73.5268 },
};

export const DEFAULT_COORD = { lat: 22.2587, lng: 71.1924 }; // Center of Gujarat loosely
