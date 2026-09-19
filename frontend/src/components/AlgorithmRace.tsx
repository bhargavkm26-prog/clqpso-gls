import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Play, RotateCcw } from 'lucide-react';

export default function AlgorithmRace() {
  const [data, setData] = useState<any[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [iteration, setIteration] = useState(0);

  const MAX_ITERATIONS = 200;

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && iteration < MAX_ITERATIONS) {
      interval = setInterval(() => {
        setIteration((prev) => prev + 1);
        setData((prevData) => {
          const i = prevData.length;
          
          // Simulated curves
          // CLQPSO converges fast and low
          const clqpso = 1000 + 4000 * Math.exp(-i / 20) + (Math.random() * 50);
          
          // PSO converges slower and gets stuck in local optima
          const pso = 1300 + 3700 * Math.exp(-i / 40) + (Math.random() * 80);
          
          // GA converges even slower
          const ga = 1500 + 3500 * Math.exp(-i / 80) + (Math.random() * 100);

          return [...prevData, { iteration: i, clqpso, pso, ga }];
        });
      }, 50); // 50ms per iteration
    } else if (iteration >= MAX_ITERATIONS) {
      setIsPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isPlaying, iteration]);

  const handleStart = () => {
    if (iteration >= MAX_ITERATIONS) {
      setData([]);
      setIteration(0);
    }
    setIsPlaying(true);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setData([]);
    setIteration(0);
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800">Algorithm Race</h3>
          <p className="text-xs text-slate-500">CLQPSO-GLS vs Classical PSO vs GA</p>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={handleStart}
            disabled={isPlaying}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Play className="h-4 w-4 mr-1" /> {iteration === 0 ? 'Start Race' : 'Resume'}
          </button>
          <button 
            onClick={handleReset}
            className="flex items-center px-3 py-1.5 bg-slate-100 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
          >
            <RotateCcw className="h-4 w-4 mr-1" /> Reset
          </button>
        </div>
      </div>
      
      <div className="h-64 w-full">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400 bg-slate-50 rounded-lg border border-dashed border-slate-300">
            Click Start Race to begin simulation
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="iteration" 
                tick={{ fontSize: 12, fill: '#64748b' }} 
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis 
                domain={['auto', 'auto']} 
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
                tickFormatter={(value) => value.toFixed(0)}
              />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                labelStyle={{ fontWeight: 'bold', color: '#334155' }}
              />
              <Legend verticalAlign="top" height={36}/>
              <Line type="monotone" name="CLQPSO-GLS" dataKey="clqpso" stroke="#4f46e5" strokeWidth={3} dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Standard PSO" dataKey="pso" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Genetic Algorithm" dataKey="ga" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      
      {/* Mini leaderboard */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-100">
            <div className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">CLQPSO-GLS</div>
            <div className="text-xl font-bold text-indigo-900">{data[data.length - 1].clqpso.toFixed(1)}</div>
          </div>
          <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
            <div className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-1">PSO</div>
            <div className="text-xl font-bold text-amber-900">{data[data.length - 1].pso.toFixed(1)}</div>
          </div>
          <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-100">
            <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">GA</div>
            <div className="text-xl font-bold text-emerald-900">{data[data.length - 1].ga.toFixed(1)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
