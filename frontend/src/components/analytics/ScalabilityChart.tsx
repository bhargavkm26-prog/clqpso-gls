import React from 'react';
import { LineChart, ArrowUpRight } from 'lucide-react';

export default function ScalabilityChart() {
  const data = [
    { customers: 32, runtime: 0.12, cost: 952.5 },
    { customers: 53, runtime: 0.28, cost: 1199.6 },
    { customers: 80, runtime: 0.65, cost: 1554.5 },
    { customers: 100, runtime: 1.15, cost: 1890.2 },
    { customers: 150, runtime: 2.45, cost: 2478.2 },
    { customers: 200, runtime: 4.82, cost: 3490.9 },
  ];

  const maxRuntime = 5.0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
      <div className="flex justify-between items-center border-b border-slate-100 pb-2">
        <div className="flex items-center space-x-2">
          <LineChart className="h-4 w-4 text-indigo-600" />
          <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Algorithmic Scalability (CPU Runtime vs Customers)</h4>
        </div>
        <span className="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-semibold flex items-center">
          <ArrowUpRight className="h-3 w-3 mr-0.5" /> O(n) Split Decoder
        </span>
      </div>

      <div className="space-y-2">
        {data.map((item, idx) => {
          const barWidth = Math.min((item.runtime / maxRuntime) * 100, 100);
          return (
            <div key={idx} className="text-xs">
              <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-0.5">
                <span>{item.customers} Customers ({item.cost.toFixed(0)} cost)</span>
                <span className="font-mono text-slate-800 font-bold">{item.runtime.toFixed(2)}s</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
