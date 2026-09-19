import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Play, RotateCcw } from 'lucide-react';

export default function AlgorithmRace() {
  const [data, setData] = useState<any[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [iteration, setIteration] = useState(0);

  const MAX_ITERATIONS = 200;

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
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
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-between items-center mb-2 shrink-0">
        <div>
          {/* Title removed, as Dashboard already provides it */}
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={handleStart}
            disabled={isPlaying}
            className="flex items-center px-2 py-1 bg-indigo-600 text-white text-[10px] font-bold rounded-md hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-sm uppercase tracking-wider"
          >
            <Play className="h-3 w-3 mr-1" /> {iteration === 0 ? 'Start Race' : 'Resume'}
          </button>
          <button 
            onClick={handleReset}
            className="flex items-center px-2 py-1 bg-slate-700 border border-slate-600 text-slate-200 text-[10px] font-bold rounded-md hover:bg-slate-600 transition-colors shadow-sm uppercase tracking-wider"
          >
            <RotateCcw className="h-3 w-3 mr-1" /> Reset
          </button>
        </div>
      </div>
      
      <div className="flex-1 min-h-[80px] w-full relative">
        {data.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400 font-medium text-[10px] uppercase tracking-wider border border-dashed border-slate-700 rounded bg-slate-800/30">
            Click Start to simulate race
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.5} />
              <XAxis 
                dataKey="iteration" 
                tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }} 
                tickLine={false}
                axisLine={false}
                dy={10}
              />
              <YAxis 
                domain={['auto', 'auto']} 
                tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toFixed(0)}
              />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#0f172a', padding: '6px 10px' }}
                labelStyle={{ fontWeight: 'bold', color: '#94a3b8', fontSize: '10px', marginBottom: '2px' }}
                itemStyle={{ fontSize: '11px', fontWeight: 'bold' }}
              />
              <Legend verticalAlign="top" height={20} iconType="circle" wrapperStyle={{ fontSize: '9px', fontWeight: 600, color: '#94a3b8' }}/>
              <Line type="monotone" name="CLQPSO-GLS" dataKey="clqpso" stroke="#6366f1" strokeWidth={3} dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Standard PSO" dataKey="pso" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Genetic Algorithm" dataKey="ga" stroke="#10b981" strokeWidth={2} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      
      {/* Mini leaderboard */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-2 mt-2 shrink-0">
          <div className="bg-indigo-900/30 rounded p-1.5 border border-indigo-500/30">
            <div className="text-[8px] font-bold text-indigo-400 uppercase tracking-widest mb-0.5">CLQPSO-GLS</div>
            <div className="text-xs font-black text-indigo-300 font-mono tracking-tighter">{data[data.length - 1].clqpso.toFixed(0)}</div>
          </div>
          <div className="bg-amber-900/30 rounded p-1.5 border border-amber-500/30">
            <div className="text-[8px] font-bold text-amber-400 uppercase tracking-widest mb-0.5">Classic PSO</div>
            <div className="text-xs font-black text-amber-300 font-mono tracking-tighter">{data[data.length - 1].pso.toFixed(0)}</div>
          </div>
          <div className="bg-emerald-900/30 rounded p-1.5 border border-emerald-500/30">
            <div className="text-[8px] font-bold text-emerald-400 uppercase tracking-widest mb-0.5">Genetic Alg</div>
            <div className="text-xs font-black text-emerald-300 font-mono tracking-tighter">{data[data.length - 1].ga.toFixed(0)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
