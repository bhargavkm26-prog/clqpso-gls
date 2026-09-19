import { TrendingUp, Truck, Zap, Clock } from 'lucide-react';

interface MetricsProps {
  iteration: number;
  bestFitness: number | null;
  vehicleCount: number;
  elapsedMs?: number | null;
}

export default function MetricsSidebar({ iteration, bestFitness, vehicleCount, elapsedMs }: MetricsProps) {
  const formatTime = (ms: number | null | undefined) => {
    if (!ms) return '---';
    if (ms < 1000) return `${ms.toFixed(0)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  };

  return (
    <div className="space-y-4">
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
          {iteration} <span className="text-sm font-semibold text-slate-500 ml-2">/ 1000</span>
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
    </div>
  );
}
