import axios from 'axios';
import { API_BASE_URL } from './constants';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const acknowledgeAlert = async (alertId, agency) => {
  const response = await api.post('/api/acknowledge', {
    alert_id: alertId,
    agency: agency,
  });
  return response.data;
};

export const fetchEvents = async (location, riskLevel) => {
  const params = {};
  if (location && location !== 'All') params.location = location;
  if (riskLevel && riskLevel !== 'All') params.risk_level = riskLevel;
  
  const response = await api.get('/api/events', { params });
  return response.data;
};

export const startReplay = async () => {
  const response = await api.post('/api/replay/start');
  return response.data;
};

export const getReplayFrame = async () => {
  const response = await api.get('/api/replay/frame');
  return response.data;
};

export const resetReplay = async () => {
  const response = await api.post('/api/replay/reset');
  return response.data;
};

export default api;
