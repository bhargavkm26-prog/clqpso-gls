import { TrendingUp, Truck, Zap } from 'lucide-react';

interface MetricsProps {
  iteration: number;
  bestFitness: number | null;
  vehicleCount: number;
}

export default function MetricsSidebar({ iteration, bestFitness, vehicleCount }: MetricsProps) {
  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center text-slate-500 mb-1">
          <Zap className="h-4 w-4 mr-2 text-amber-500" />
          <span className="text-xs font-semibold uppercase tracking-wider">Best Fitness</span>
        </div>
        <div className="text-2xl font-bold text-slate-800">
          {bestFitness ? bestFitness.toFixed(2) : '---'}
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center text-slate-500 mb-1">
          <TrendingUp className="h-4 w-4 mr-2 text-emerald-500" />
          <span className="text-xs font-semibold uppercase tracking-wider">Iteration</span>
        </div>
        <div className="text-2xl font-bold text-slate-800">
          {iteration} <span className="text-sm font-normal text-slate-400">/ 1000</span>
        </div>
      </div>
      
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center text-slate-500 mb-1">
          <Truck className="h-4 w-4 mr-2 text-indigo-500" />
          <span className="text-xs font-semibold uppercase tracking-wider">Active Vehicles</span>
        </div>
        <div className="text-2xl font-bold text-slate-800">
          {vehicleCount}
        </div>
      </div>
    </div>
  );
}
