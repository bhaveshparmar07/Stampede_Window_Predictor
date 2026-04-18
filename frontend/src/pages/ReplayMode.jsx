import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, FastForward, Rewind, Info } from 'lucide-react';
import { startReplay, getReplayFrame, resetReplay } from '../utils/api';
import PressureGauge from '../components/PressureGauge';
import CrushCountdown from '../components/CrushCountdown';
import SurgeClassifier from '../components/SurgeClassifier';
import AlertBanner from '../components/AlertBanner';
import FlowChart from '../components/FlowChart';

const ReplayMode = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [frame, setFrame] = useState(null);
  const [history, setHistory] = useState([]);
  const [totalFrames, setTotalFrames] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);
  
  const timerRef = useRef(null);

  // Initialize Replay
  const initReplay = async () => {
    try {
      const res = await startReplay();
      if (res.status === 'ok') {
        setTotalFrames(res.total_frames);
        setIsLoaded(true);
        fetchNextFrame();
      }
    } catch (err) {
      console.error("Failed to load replay:", err);
    }
  };

  useEffect(() => {
    initReplay();
    return () => clearInterval(timerRef.current);
  }, []);

  // Frame Fetching
  const fetchNextFrame = async () => {
    try {
      const res = await getReplayFrame();
      if (res.status === 'done') {
        setIsPlaying(false);
        return;
      }
      
      const newFrame = res.data;
      setFrame(newFrame);
      setProgress((res.frame_index / res.total_frames) * 100);
      
      setHistory(prev => {
        const next = [...prev, {
          timestamp: newFrame.timestamp,
          entry: newFrame.entry_flow_rate_pax_per_min,
          exit: newFrame.exit_flow_rate_pax_per_min,
          pressure: newFrame.pressure_index,
          label: newFrame.event_label
        }];
        return next.length > 50 ? next.slice(-50) : next;
      });
      
    } catch (err) {
      console.error("Error fetching frame", err);
      setIsPlaying(false);
    }
  };

  // Playback Control Effect
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        fetchNextFrame();
      }, 1000 / speed);
    } else {
      clearInterval(timerRef.current);
    }
    
    return () => clearInterval(timerRef.current);
  }, [isPlaying, speed]);

  const handleReset = async () => {
    setIsPlaying(false);
    setHistory([]);
    setFrame(null);
    setProgress(0);
    clearInterval(timerRef.current);
    try {
      await resetReplay();
      fetchNextFrame();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isLoaded) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        Loading Replay Scenario...
      </div>
    );
  }

  // Derive alert state from event label for demo
  const isAlertFired = frame && ['alert_fired', 'acknowledged_police', 'acknowledged_temple', 'acknowledged_transport', 'peak', 'resolving'].includes(frame.event_label);
  
  const mockAlert = isAlertFired ? {
    location: frame.location,
    pressure_index: frame.pressure_index,
    classification: 'GENUINE CRUSH BUILDUP',
    crush_window_min: frame.predicted_crush_window
  } : null;

  // Derive classifier from label
  let classification = "MONITORING";
  if (frame) {
    if (['crush_build', 'classifier_fires', 'alert_fired'].includes(frame.event_label)) {
      classification = "GENUINE CRUSH BUILDUP";
    } else if (frame.event_label === "surge_start") {
       // Just visual flavor for replay
       classification = "MOMENTARY SURGE — SELF-RESOLVING";
    }
  }

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Replay Mode</h1>
          <p className="text-slate-500 text-sm mt-1">Review pre-recorded near-crush scenario.</p>
        </div>
        
        {/* Controls */}
        <div className="flex items-center space-x-4 bg-slate-900 border border-slate-700 py-2 px-4 rounded-full">
          <button 
            onClick={handleReset} 
            className="p-2 text-slate-500 hover:text-white transition"
            title="Reset to beginning"
          >
            <Rewind size={20} />
          </button>
          
          <button 
            onClick={() => setIsPlaying(!isPlaying)} 
            className="w-12 h-12 flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white rounded-full transition shadow-lg shadow-blue-900/50"
          >
            {isPlaying ? <Square size={20} fill="currentColor" /> : <Play size={20} className="ml-1" fill="currentColor" />}
          </button>
          
          <div className="flex space-x-1 pl-2 border-l border-slate-700">
            {[1, 2, 4].map(s => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`w-8 h-8 rounded text-sm font-bold transition ${speed === s ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'}`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>

      <AlertBanner alert={mockAlert} currentPressure={frame?.pressure_index || 0} />

      <div className="grid grid-cols-12 gap-6">
        
        <div className="col-span-12 xl:col-span-4 bg-slate-950 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center font-bold mb-6 text-slate-300">
            <Info size={18} className="mr-2 text-blue-400" /> Scenario Event Phase
          </div>
          
          <div className="text-2xl font-mono font-bold text-white mb-8 border-b border-slate-800 pb-4 uppercase tracking-widest text-center">
            {frame ? frame.event_label.replace(/_/g, ' ') : 'Waiting...'}
          </div>

          <SurgeClassifier classification={classification} />
          
          <div className="mt-8 flex justify-center">
            <CrushCountdown 
              minutes={frame?.predicted_crush_window || 15} 
              isSafe={!frame || frame.pressure_index < 40 || frame.risk_level === 'Low'}
            />
          </div>
        </div>

        <div className="col-span-12 md:col-span-6 xl:col-span-4 bg-slate-950 border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center">
          <h2 className="text-slate-500 uppercase tracking-widest text-sm font-bold mb-6">Pressure Index</h2>
          <PressureGauge value={frame?.pressure_index || 0} size="lg" />
        </div>

        <div className="col-span-12 md:col-span-6 xl:col-span-4 bg-slate-950 border border-slate-800 rounded-xl p-6 flex flex-col">
          <h2 className="text-slate-500 uppercase tracking-widest text-sm font-bold mb-4">Replay Flow Dynamics</h2>
          <div className="flex-1">
             <FlowChart data={history} />
          </div>
        </div>

      </div>

      {/* Timeline Bar */}
      <div className="mt-auto bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex justify-between text-xs text-slate-500 mb-2 font-mono">
          <span>{frame ? frame.timestamp.split('T')[1] : '00:00:00'}</span>
          <span>{progress.toFixed(0)}%</span>
        </div>
        <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-300 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
    </div>
  );
};

export default ReplayMode;
