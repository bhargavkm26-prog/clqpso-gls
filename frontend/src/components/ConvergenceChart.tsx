import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartProps {
  data: { iteration: number; cost: number }[];
}

export default function ConvergenceChart({ data }: ChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center text-slate-400 text-sm">
        Start optimization to view convergence curve
      </div>
    );
  }

  // Calculate dynamic Y-axis bounds for better visualization
  const minCost = Math.min(...data.map(d => d.cost));
  const maxCost = Math.max(...data.map(d => d.cost));
  const padding = (maxCost - minCost) * 0.1 || maxCost * 0.1;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
        <XAxis 
          dataKey="iteration" 
          tick={{ fontSize: 12, fill: '#64748b' }} 
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
        />
        <YAxis 
          domain={[minCost - padding, maxCost + padding]} 
          tick={{ fontSize: 12, fill: '#64748b' }}
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
          tickFormatter={(value) => value.toFixed(0)}
        />
        <Tooltip 
          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
          labelStyle={{ fontWeight: 'bold', color: '#334155' }}
          itemStyle={{ color: '#4f46e5' }}
        />
        <Line 
          type="monotone" 
          dataKey="cost" 
          stroke="#4f46e5" 
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6, fill: '#4f46e5', stroke: '#fff', strokeWidth: 2 }}
          isAnimationActive={false} // Disable animation for real-time updates
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
