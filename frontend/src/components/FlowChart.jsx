import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceArea } from 'recharts';
import { format } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl shrink-0">
        <p className="text-slate-300 text-xs mb-2">
          {label ? format(new Date(label), 'HH:mm:ss') : ''}
        </p>
        {payload.map((p, i) => (
          <div key={i} className="flex flex-col mb-1">
            <span className="text-xs uppercase tracking-wider font-semibold" style={{ color: p.color }}>
              {p.name}
            </span>
            <span className="text-lg font-bold text-white">
              {p.value?.toFixed(1) || 0}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const FlowChart = ({ data = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center border border-slate-800 rounded-xl bg-slate-900/50">
        <span className="text-slate-500 text-sm">Waiting for flow data...</span>
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(tick) => {
              try {
                return format(new Date(tick), 'HH:mm');
              } catch (e) {
                return '';
              }
            }}
            stroke="#475569" 
            tick={{ fill: '#64748b', fontSize: 12 }} 
            dy={10}
            minTickGap={30}
          />
          
          <YAxis 
            stroke="#475569" 
            tick={{ fill: '#64748b', fontSize: 12 }} 
            axisLine={false}
            tickLine={false}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend 
            wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} 
            iconType="circle" 
          />
          
          {/* Highlight dangerous pressure buildup */}
          <ReferenceArea y1={70} y2={100} fill="#ef4444" fillOpacity={0.05} />
          
          <Line 
            type="monotone" 
            dataKey="entry" 
            name="Entry Flow" 
            stroke="#3b82f6" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ r: 6, strokeWidth: 0 }}
            isAnimationActive={false}
          />
          
          <Line 
            type="monotone" 
            dataKey="exit" 
            name="Exit Flow" 
            stroke="#10b981" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ r: 6, strokeWidth: 0 }}
            isAnimationActive={false}
          />
          
          <Line 
            type="monotone" 
            dataKey="pressure" 
            name="Pressure Index" 
            stroke="#f59e0b" 
            strokeWidth={3}
            strokeDasharray="5 5" 
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FlowChart;
