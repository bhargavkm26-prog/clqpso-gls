import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartProps {
  data: { iteration: number; cost: number }[];
}

export default function ConvergenceChart({ data }: ChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center text-slate-400 text-sm font-medium">
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
      <AreaChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
        <XAxis 
          dataKey="iteration" 
          tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }} 
          tickLine={false}
          axisLine={false}
          dy={10}
        />
        <YAxis 
          domain={[minCost - padding, maxCost + padding]} 
          tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => {
            const range = maxCost - minCost;
            if (range === 0 || range < 5) return value.toFixed(2);
            if (range < 50) return value.toFixed(1);
            return value.toFixed(0);
          }}
        />
        <Tooltip 
          contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', padding: '8px 12px' }}
          labelStyle={{ fontWeight: 'bold', color: '#64748b', fontSize: '12px', marginBottom: '4px' }}
          itemStyle={{ color: '#4f46e5', fontWeight: 'bold', fontSize: '14px' }}
        />
        <Area 
          type="monotone" 
          dataKey="cost" 
          stroke="#6366f1" 
          strokeWidth={3}
          fillOpacity={1}
          fill="url(#colorCost)"
          isAnimationActive={false} // Disable animation for real-time updates
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
