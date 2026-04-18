import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { PRESSURE_THRESHOLDS, LOCATION_COORDS, DEFAULT_COORD } from '../utils/constants';

// Update Leaflet map view based on active location
const MapUpdater = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView([center.lat, center.lng], map.getZoom());
    }
  }, [center, map]);
  return null;
};

// Custom HTML marker icon to allow Tailwind and dynamic colors
const createCustomIcon = (pressureValue) => {
  let color = PRESSURE_THRESHOLDS.safe.color;
  if (pressureValue >= PRESSURE_THRESHOLDS.watch.min) color = PRESSURE_THRESHOLDS.watch.color;
  if (pressureValue >= PRESSURE_THRESHOLDS.critical.min) color = PRESSURE_THRESHOLDS.critical.color;

  const isBlinking = pressureValue >= PRESSURE_THRESHOLDS.critical.min;

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="position: relative; width: 24px; height: 24px;">
        ${isBlinking ? `<div style="position: absolute; inset: -4px; border-radius: 50%; background-color: ${color}; opacity: 0.4; animation: pulse 1.5s infinite;"></div>` : ''}
        <div style="position: absolute; inset: 0; border-radius: 50%; background-color: ${color}; border: 3px solid #1e293b; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
};

const CorridorMap = ({ locations, activeLocation, pressureData }) => {
  const centerCoord = activeLocation && LOCATION_COORDS[activeLocation] 
    ? LOCATION_COORDS[activeLocation] 
    : DEFAULT_COORD;

  return (
    <div className="w-full h-full rounded-xl overflow-hidden border border-slate-700 relative z-0">
      <MapContainer 
        center={[centerCoord.lat, centerCoord.lng]} 
        zoom={11} 
        style={{ height: '100%', width: '100%', background: '#0f172a' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        <MapUpdater center={centerCoord} />

        {locations.map((loc) => {
          // Check if coordinate exists or provide default offset
          const coord = LOCATION_COORDS[loc] || { 
            lat: DEFAULT_COORD.lat + (Math.random() * 0.1 - 0.05), 
            lng: DEFAULT_COORD.lng + (Math.random() * 0.1 - 0.05) 
          };
          
          const pressure = pressureData[loc] || 0;
          
          return (
            <Marker key={loc} position={[coord.lat, coord.lng]} icon={createCustomIcon(pressure)}>
              <Popup className="custom-popup">
                <div className="font-bold text-white text-sm mb-1">{loc}</div>
                <div className="text-slate-300 text-xs font-medium">Pressure Index: {pressure.toFixed(1)}</div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default CorridorMap;
