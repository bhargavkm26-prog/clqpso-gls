import { TrendingUp, Truck, Zap, Clock, Trophy } from 'lucide-react';

interface MetricsProps {
  iteration: number;
  bestFitness: number | null;
  vehicleCount: number;
  elapsedMs?: number | null;
  benchmarkData?: any[] | null;
}

export default function MetricsSidebar({ iteration, bestFitness, vehicleCount, elapsedMs, benchmarkData }: MetricsProps) {
  const formatTime = (ms: number | null | undefined) => {
    if (!ms) return '---';
    if (ms < 1000) return `${ms.toFixed(0)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  };

  return (
    <div className="space-y-4 p-4 h-full overflow-y-auto">
      <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/50 shadow-inner relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150"></div>
        <div className="flex items-center text-slate-400 mb-2 relative z-10">
          <Zap className="h-4 w-4 mr-2 text-amber-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest">Best Fitness</span>
        </div>
        <div className="text-3xl font-black text-white font-mono tracking-tight relative z-10">
          {bestFitness ? bestFitness.toFixed(2) : '---'}
        </div>
      </div>
      
      <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/50 shadow-inner relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150"></div>
        <div className="flex items-center text-slate-400 mb-2 relative z-10">
          <Clock className="h-4 w-4 mr-2 text-blue-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest">Elapsed Time</span>
        </div>
        <div className="text-3xl font-black text-white font-mono tracking-tight relative z-10">
          {formatTime(elapsedMs)}
        </div>
      </div>
      
      <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/50 shadow-inner relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150"></div>
        <div className="flex items-center text-slate-400 mb-2 relative z-10">
          <TrendingUp className="h-4 w-4 mr-2 text-emerald-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest">Iteration</span>
        </div>
        <div className="text-3xl font-black text-white font-mono tracking-tight flex items-baseline relative z-10">
          {iteration}
        </div>
      </div>
      
      <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/50 shadow-inner relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150"></div>
        <div className="flex items-center text-slate-400 mb-2 relative z-10">
          <Truck className="h-4 w-4 mr-2 text-indigo-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest">Active Routes</span>
        </div>
        <div className="text-3xl font-black text-white font-mono tracking-tight relative z-10">
          {vehicleCount}
        </div>
      </div>

      {benchmarkData && (
        <div className="mt-8 animate-[slideIn_0.3s_ease_forwards]">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center">
            <Trophy className="w-4 h-4 mr-2 text-yellow-500" /> Live Showdown Results
          </h3>
          <div className="space-y-3">
            {benchmarkData.map((b, i) => {
              const isWinner = b.algorithm === 'CLQPSO-GLS';
              return (
                <div key={i} className={`p-3 rounded-lg border ${isWinner ? 'bg-indigo-900/40 border-indigo-500/50' : 'bg-slate-800/50 border-slate-700/50'}`}>
                  <div className="flex justify-between items-center mb-1">
                    <span className={`text-sm font-bold ${isWinner ? 'text-indigo-300' : 'text-slate-300'}`}>
                      {b.algorithm}
                    </span>
                    {isWinner && <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded uppercase font-bold tracking-wider">Winner</span>}
                  </div>
                  <div className="flex justify-between text-xs mt-2">
                    <div className="flex flex-col">
                      <span className="text-slate-500 font-medium">Cost</span>
                      <span className={`font-mono font-bold ${isWinner ? 'text-emerald-400' : 'text-slate-200'}`}>
                        {b.cost.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-slate-500 font-medium">Time</span>
                      <span className={`font-mono font-bold ${isWinner ? 'text-blue-400' : 'text-slate-200'}`}>
                        {b.time.toFixed(3)}s
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
