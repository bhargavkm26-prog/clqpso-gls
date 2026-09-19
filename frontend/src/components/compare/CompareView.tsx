import React from 'react';
import { LineChart } from 'lucide-react';
import AlgorithmRace from './AlgorithmRace';
import AlgorithmComparisonTable from './AlgorithmComparisonTable';
import BenchmarkPanel from './BenchmarkPanel';

export default function CompareView() {
  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-full">
      {/* Top Convergence Performance Comparison Line Chart */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <LineChart className="h-5 w-5 text-indigo-600" />
            <h3 className="font-bold text-slate-800 text-sm">Convergence Performance (Log-Scale Cost vs Iterations)</h3>
          </div>
          <span className="text-[10px] bg-indigo-50 text-indigo-700 font-bold px-2.5 py-1 rounded-full">
            Real-time Race
          </span>
        </div>

        <div className="h-64">
          <AlgorithmRace />
        </div>
      </div>

      {/* Primary Algorithm Performance Comparison Table */}
      <AlgorithmComparisonTable />

      {/* Secondary Benchmark Comparison Suite */}
      <BenchmarkPanel />
    </div>
  );
}
