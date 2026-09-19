import { useEffect, useState } from 'react';
import { Award, CheckCircle, Table } from 'lucide-react';

interface BenchmarkRow {
  instance: string;
  algorithm: string;
  mean: number;
  std: number;
  best: number;
  worst: number;
  median: number;
  mean_runtime: number;
  gap_percent: number | null;
  valid: boolean;
}

export default function BenchmarkPanel() {
  const [data, setData] = useState<BenchmarkRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedInstance, setSelectedInstance] = useState<string>('A-n32-k5');

  useEffect(() => {
    fetch('http://localhost:8000/api/benchmarks')
      .then(res => res.json())
      .then(res => {
        if (res.status === 'success' && res.benchmarks) {
          setData(res.benchmarks);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredData = data.filter(d => d.instance === selectedInstance);

  const minCost = filteredData.length > 0 ? Math.min(...filteredData.map(d => d.mean)) : 0;
  const minTime = filteredData.length > 0 ? Math.min(...filteredData.map(d => d.mean_runtime)) : 0;
  const minGap = filteredData.length > 0 ? Math.min(...filteredData.map(d => d.gap_percent ?? 999)) : 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Table className="h-5 w-5 text-indigo-600" />
          <h3 className="font-bold text-slate-800 text-base">Phase 9 CVRP Benchmark Comparison Suite</h3>
        </div>

        <div className="flex space-x-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
          {['A-n32-k5', 'A-n53-k7', 'A-n80-k10'].map(inst => (
            <button
              key={inst}
              onClick={() => setSelectedInstance(inst)}
              className={`px-3 py-1.5 rounded-md transition-all ${
                selectedInstance === inst
                  ? 'bg-white text-blue-700 shadow-sm font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {inst}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-slate-400 text-xs animate-pulse">
          Loading benchmark results...
        </div>
      ) : filteredData.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs">
          No benchmark runs recorded for {selectedInstance}. Execute <code className="bg-slate-100 px-2 py-1 rounded">python -m backend.benchmarks.runner</code> to populate.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-700">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Algorithm</th>
                <th className="py-3 px-4 text-right">Mean Cost</th>
                <th className="py-3 px-4 text-right">Std</th>
                <th className="py-3 px-4 text-right">Best Cost</th>
                <th className="py-3 px-4 text-right">Runtime (s)</th>
                <th className="py-3 px-4 text-right">Gap to BKS (%)</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredData.map((row, idx) => {
                const isBestCost = Math.abs(row.mean - minCost) < 1e-2;
                const isBestTime = Math.abs(row.mean_runtime - minTime) < 1e-2;
                const isBestGap = row.gap_percent !== null && Math.abs(row.gap_percent - minGap) < 1e-2;

                return (
                  <tr 
                    key={idx} 
                    className={`hover:bg-slate-50 transition-colors ${
                      row.algorithm.includes('CLQPSO') ? 'bg-indigo-50/40 font-medium' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-bold text-slate-800 flex items-center">
                      {row.algorithm.includes('CLQPSO') && (
                        <Award className="h-4 w-4 text-indigo-600 mr-1.5 shrink-0" />
                      )}
                      {row.algorithm}
                    </td>
                    <td className={`py-3 px-4 text-right font-mono font-bold ${isBestCost ? 'text-emerald-600 bg-emerald-50/60 rounded' : 'text-slate-800'}`}>
                      {row.mean.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-500">
                      ±{row.std.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-700">
                      {row.best.toFixed(2)}
                    </td>
                    <td className={`py-3 px-4 text-right font-mono ${isBestTime ? 'text-blue-600 font-bold bg-blue-50/60 rounded' : 'text-slate-600'}`}>
                      {row.mean_runtime.toFixed(3)}s
                    </td>
                    <td className={`py-3 px-4 text-right font-mono ${isBestGap ? 'text-emerald-700 font-bold bg-emerald-100/70 rounded' : 'text-slate-700'}`}>
                      {row.gap_percent !== null ? `${row.gap_percent.toFixed(2)}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {row.valid ? (
                        <span className="inline-flex items-center text-emerald-600 font-bold text-[10px]">
                          <CheckCircle className="h-3.5 w-3.5 mr-0.5" /> Valid
                        </span>
                      ) : (
                        <span className="text-rose-500 font-bold text-[10px]">Invalid</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
