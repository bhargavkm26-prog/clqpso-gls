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
      <div className="flex justify-between items-center mb-3 shrink-0">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center uppercase tracking-wider">Algorithm Race</h3>
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mt-0.5">CLQPSO-GLS vs PSO vs GA</p>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={handleStart}
            disabled={isPlaying}
            className="flex items-center px-3 py-1.5 bg-indigo-600 text-white text-xs font-bold rounded-md hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-sm uppercase tracking-wider"
          >
            <Play className="h-3 w-3 mr-1" /> {iteration === 0 ? 'Start Race' : 'Resume'}
          </button>
          <button 
            onClick={handleReset}
            className="flex items-center px-3 py-1.5 bg-white border border-slate-200 text-slate-600 text-xs font-bold rounded-md hover:bg-slate-50 transition-colors shadow-sm uppercase tracking-wider"
          >
            <RotateCcw className="h-3 w-3 mr-1" /> Reset
          </button>
        </div>
      </div>
      
      <div className="flex-1 min-h-0 w-full relative">
        {data.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400 font-medium text-sm border-2 border-dashed border-slate-200 rounded-lg bg-slate-50/50">
            Click Start Race to begin simulation
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
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
                contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', padding: '8px 12px' }}
                labelStyle={{ fontWeight: 'bold', color: '#64748b', fontSize: '12px', marginBottom: '4px' }}
              />
              <Legend verticalAlign="top" height={30} iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: 600, color: '#64748b' }}/>
              <Line type="monotone" name="CLQPSO-GLS" dataKey="clqpso" stroke="#6366f1" strokeWidth={3} dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Standard PSO" dataKey="pso" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} isAnimationActive={false} />
              <Line type="monotone" name="Genetic Algorithm" dataKey="ga" stroke="#10b981" strokeWidth={2} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      
      {/* Mini leaderboard */}
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mt-4 shrink-0">
          <div className="bg-indigo-50/50 rounded-lg p-2.5 border border-indigo-100/50">
            <div className="text-[9px] font-bold text-indigo-500 uppercase tracking-widest mb-1">CLQPSO-GLS</div>
            <div className="text-lg font-black text-indigo-700 font-mono tracking-tighter">{data[data.length - 1].clqpso.toFixed(1)}</div>
          </div>
          <div className="bg-amber-50/50 rounded-lg p-2.5 border border-amber-100/50">
            <div className="text-[9px] font-bold text-amber-500 uppercase tracking-widest mb-1">Classic PSO</div>
            <div className="text-lg font-black text-amber-700 font-mono tracking-tighter">{data[data.length - 1].pso.toFixed(1)}</div>
          </div>
          <div className="bg-emerald-50/50 rounded-lg p-2.5 border border-emerald-100/50">
            <div className="text-[9px] font-bold text-emerald-500 uppercase tracking-widest mb-1">Genetic Alg</div>
            <div className="text-lg font-black text-emerald-700 font-mono tracking-tighter">{data[data.length - 1].ga.toFixed(1)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
