import { useState, useEffect } from 'react';

export default function HistoryView() {
  const [benchmarks, setBenchmarks] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/benchmarks')
      .then(res => res.json())
      .then(data => setBenchmarks(data))
      .catch(e => console.error(e));
  }, []);

  return (
    <div className="p-6 text-white h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Benchmark Results</h2>
        <p className="text-sm text-slate-400">
          This table compares the proposed CLQPSO-GLS algorithm against established Best Known Solutions (BKS) for standard routing problems. A smaller <strong className="text-slate-300">"Gap to BKS"</strong> indicates higher accuracy, demonstrating the algorithm's capability to find near-optimal paths compared to existing methods.
        </p>
      </div>
      <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-700">
              <th className="p-3">Instance</th>
              <th className="p-3">Mean Cost</th>
              <th className="p-3">Best Cost</th>
              <th className="p-3">Runtime (s)</th>
              <th className="p-3">Gap to BKS (%)</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {benchmarks.map((b, i) => (
              <tr key={i} className="border-t border-slate-700 hover:bg-slate-700/50">
                <td className="p-3">{b.name}</td>
                <td className="p-3">{b.mean_cost.toFixed(2)}</td>
                <td className="p-3 text-emerald-400 font-bold">{b.best_cost.toFixed(2)}</td>
                <td className="p-3">{b.runtime_s.toFixed(3)}</td>
                <td className="p-3">{b.gap_to_bks.toFixed(2)}%</td>
                <td className="p-3">
                  <span className="px-2 py-1 bg-emerald-900/50 text-emerald-400 rounded text-xs">{b.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
