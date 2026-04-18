import React, { useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';

const AlertBanner = ({ alert, currentPressure }) => {
  const audioCtxRef = useRef(null);
  const unlockedRef = useRef(false);

  const getAudioContext = () => {
    if (audioCtxRef.current) return audioCtxRef.current;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    audioCtxRef.current = new Ctx();
    return audioCtxRef.current;
  };

  useEffect(() => {
    const unlockAudio = async () => {
      unlockedRef.current = true;
      const ctx = getAudioContext();
      if (ctx && ctx.state === 'suspended') {
        try {
          await ctx.resume();
        } catch (err) {
          console.error('[ALERT_AUDIO] Failed to resume context:', err);
        }
      }
    };

    window.addEventListener('pointerdown', unlockAudio, { once: true });
    window.addEventListener('keydown', unlockAudio, { once: true });
    window.addEventListener('touchstart', unlockAudio, { once: true });

    return () => {
      window.removeEventListener('pointerdown', unlockAudio);
      window.removeEventListener('keydown', unlockAudio);
      window.removeEventListener('touchstart', unlockAudio);
    };
  }, []);

  useEffect(() => {
    if (!alert) return;
    const pressureNow = Number.isFinite(currentPressure) ? currentPressure : Number(alert.pressure_index || 0);
    const shouldPlaySound = pressureNow >= 70 || alert.status === 'active';
    if (!shouldPlaySound) return;

    const playBeep = async () => {
      if (!unlockedRef.current || document.hidden) return;
      const audioCtx = getAudioContext();
      if (!audioCtx) return;

      if (audioCtx.state === 'suspended') {
        try {
          await audioCtx.resume();
        } catch (err) {
          console.error('[ALERT_AUDIO] Failed to resume before beep:', err);
          return;
        }
      }

      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.type = 'square';
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
      oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.1); // Drop to A4

      gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.5);
    };

    // Play immediately and then interval
    playBeep();
    const interval = setInterval(playBeep, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [alert, currentPressure]);

  useEffect(() => {
    return () => {
      if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
        audioCtxRef.current.close().catch((err) => console.error('[ALERT_AUDIO] Failed to close context:', err));
      }
    };
  }, []);

  if (!alert) return null;

  return (
    <div className="w-full bg-red-600 text-white rounded-lg shadow-lg shadow-red-900/50 mb-6 overflow-hidden border border-red-500 flex flex-col md:flex-row items-center justify-between animate-in fade-in slide-in-from-top-4 duration-300">
      <div className="flex items-center space-x-4 p-4 w-full">
        <div className="p-2 bg-red-700/50 rounded-full animate-pulse">
          <AlertTriangle size={28} className="text-red-100" />
        </div>
        <div>
          <h2 className="text-xl font-bold tracking-wide uppercase flex items-center space-x-2">
            <span>Critical Alert Active</span>
            <span className="opacity-75">—</span>
            <span>{alert.location}</span>
          </h2>
          <p className="text-red-200 mt-1 font-medium">
            Triggered at 70+ • Current Live Pressure: <span className="text-white font-bold text-lg">{currentPressure !== undefined ? currentPressure.toFixed(1) : alert.pressure_index}</span> • 
            Status: <span className="text-white font-bold">{currentPressure < 40 ? 'RESOLVING (Awaiting Acknowledgment)' : alert.classification}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AlertBanner;
