import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import AlgorithmRace from './AlgorithmRace';

export default function MetricsView() {
  const [metrics, setMetrics] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(e => console.error(e));
  }, []);

  return (
    <div className="p-6 text-white h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Scaling Metrics</h2>
        <p className="text-sm text-slate-400">
          This graph illustrates how computation time scales as the number of delivery nodes increases. A flatter line indicates better scalability. Notice how CLQPSO-GLS maintains efficiency even as complexity grows, whereas traditional algorithms scale exponentially.
        </p>
      </div>
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="node_count" stroke="#94a3b8" label={{ value: 'Nodes', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
            <YAxis stroke="#94a3b8" label={{ value: 'Time (s)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
            <Legend />
            <Line type="monotone" dataKey="clqpso_time" name="CLQPSO-GLS" stroke="#10b981" strokeWidth={3} />
            <Line type="monotone" dataKey="pso_time" name="Standard PSO" stroke="#f59e0b" strokeWidth={2} />
            <Line type="monotone" dataKey="ga_time" name="Genetic Algorithm" stroke="#ef4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mb-4 mt-8">
        <h2 className="text-2xl font-bold mb-2">Algorithm Race (Cost)</h2>
        <p className="text-sm text-slate-400">
          This simulation tracks the routing cost (Y-axis) over iterations (X-axis). A steeper drop indicates faster convergence to an optimal solution. Watch how CLQPSO-GLS (Blue) rapidly finds lower-cost routes compared to standard PSO (Yellow) and Genetic Algorithm (Red).
        </p>
      </div>
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 h-96">
        <AlgorithmRace />
      </div>
    </div>
  );
}
