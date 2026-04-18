import React, { useState, useEffect } from 'react';
import { Download, Filter, Search } from 'lucide-react';
import { fetchEvents } from '../utils/api';
import { format } from 'date-fns';

const EventLog = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [filters, setFilters] = useState({
    location: 'All',
    riskLevel: 'All'
  });

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await fetchEvents(filters.location, filters.riskLevel);
      setEvents(data.events || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filters]);

  const handleExport = () => {
    if (events.length === 0) return;
    
    // Create CSV content
    const headers = ['ID', 'Timestamp', 'Location', 'Type', 'Details'];
    const rows = events.map(e => [
      e.id,
      e.timestamp,
      e.location,
      e.event_type,
      e.details.replace(/"/g, '""') // Escape quotes for CSV
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(r => `"${r.join('","')}"`)
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `events_export_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const parseDetails = (jsonStr) => {
    try {
      return JSON.parse(jsonStr);
    } catch {
      return {};
    }
  };

  const getEventStyle = (type) => {
    switch (type) {
      case 'alert_triggered': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'acknowledgement': return 'bg-green-500/10 text-green-400 border-green-500/20';
      default: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Event Archive</h1>
          <p className="text-slate-500 text-sm mt-1">Immutable audit log of all system events and agency responses.</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-1 flex">
            <span className="text-slate-500 px-3 py-1.5"><Filter size={16} /></span>
            <select 
              className="bg-transparent text-slate-300 px-2 outline-none border-l border-slate-700"
              value={filters.location}
              onChange={(e) => setFilters({...filters, location: e.target.value})}
            >
              <option value="All">All Locations</option>
              <option value="Ambaji">Ambaji</option>
              <option value="Dwarka">Dwarka</option>
              <option value="Somnath">Somnath</option>
              <option value="Pavagadh">Pavagadh</option>
            </select>
          </div>
          
          <button 
            onClick={handleExport}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium transition shadow-lg shadow-indigo-900/50"
          >
            <Download size={18} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs text-slate-500 uppercase bg-slate-950/50 sticky top-0 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 font-bold tracking-wider">Timestamp</th>
                <th className="px-6 py-4 font-bold tracking-wider">Location</th>
                <th className="px-6 py-4 font-bold tracking-wider">Event Type</th>
                <th className="px-6 py-4 font-bold tracking-wider">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                    Loading events...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                    No events found matching criteria.
                  </td>
                </tr>
              ) : (
                events.map((event) => {
                  const details = parseDetails(event.details);
                  return (
                    <tr key={event.id} className="hover:bg-slate-800/50 transition">
                      <td className="px-6 py-4 font-mono text-slate-500 whitespace-nowrap">
                        {format(new Date(event.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-200">
                        {event.location}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded inline-flex text-xs font-bold uppercase tracking-wider border ${getEventStyle(event.event_type)}`}>
                          {event.event_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs">
                        <div className="font-mono bg-slate-950 p-2 rounded text-slate-500 overflow-x-auto">
                          {Object.entries(details).map(([k, v]) => (
                            <span key={k} className="mr-3">
                              <span className="text-indigo-400">{k}:</span> {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default EventLog;
