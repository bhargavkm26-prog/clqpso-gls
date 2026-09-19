import React from 'react';
import { MapPin, Clock, Leaf, Activity, ArrowDownRight, BarChart3, LineChart } from 'lucide-react';
import AlgorithmComparisonTable from '../compare/AlgorithmComparisonTable';

export default function AnalyticsDashboard() {
  const statCards = [
    { label: 'Total Network Nodes', value: '400', unit: 'nodes', icon: MapPin, color: 'text-blue-600', trend: 'Fixed Graph', positive: true },
    { label: 'Avg. Travel Time', value: '24.5', unit: 'min', icon: Clock, color: 'text-indigo-600', trend: '-14.2% vs baseline', positive: true },
    { label: 'CO₂ Emissions', value: '142.8', unit: 'kg', icon: Leaf, color: 'text-emerald-600', trend: '-18.5% eco save', positive: true },
    { label: 'Network Efficiency', value: '94.2', unit: '%', icon: Activity, color: 'text-amber-600', trend: '+12.0% throughput', positive: true },
  ];

  const regionalTraffic = [
    { region: 'Koramangala (South)', flow: '850 veh/hr', status: 'Moderate', speed: '28 km/h', color: 'bg-amber-500' },
    { region: 'Indiranagar (East)', flow: '1,240 veh/hr', status: 'Heavy', speed: '18 km/h', color: 'bg-rose-500' },
    { region: 'MG Road (Central)', flow: '420 veh/hr', status: 'Normal', speed: '42 km/h', color: 'bg-emerald-500' },
    { region: 'HSR Layout (South-East)', flow: '610 veh/hr', status: 'Normal', speed: '38 km/h', color: 'bg-emerald-500' },
  ];

  const emissionsData = [
    { algo: 'QPSO (Ours)', emissions: 142.8, cost: 942.8, bar: 45, winner: true },
    { algo: 'Dijkstra', emissions: 191.3, cost: 1264.0, bar: 65, winner: false },
    { algo: 'A* Search', emissions: 184.2, cost: 1215.5, bar: 62, winner: false },
    { algo: 'Genetic Algorithm', emissions: 168.5, cost: 1112.0, bar: 56, winner: false },
  ];

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-full">
      {/* Top 4 Stat Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex justify-between items-center text-slate-500 text-xs font-semibold">
                <span className="uppercase tracking-wider">{card.label}</span>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
              <div className="text-2xl font-bold font-mono text-slate-800">
                {card.value} <span className="text-xs font-normal text-slate-500">{card.unit}</span>
              </div>
              <div className="flex items-center text-[11px] font-medium text-emerald-600">
                <ArrowDownRight className="h-3 w-3 mr-0.5" />
                <span>{card.trend}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Side-by-Side Analytics Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Regional Traffic Flow List / Line Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <LineChart className="h-5 w-5 text-blue-600" />
              <h3 className="font-bold text-slate-800 text-sm">Traffic Flow (Last 24 Hours by Zone)</h3>
            </div>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-mono">Bangalore Sensors</span>
          </div>

          <div className="space-y-3">
            {regionalTraffic.map((zone, i) => (
              <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-slate-50 border border-slate-200/70 text-xs">
                <div>
                  <span className="font-bold text-slate-800 block">{zone.region}</span>
                  <span className="text-[10px] text-slate-500 font-mono">Volume: {zone.flow}</span>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-slate-700 block">{zone.speed}</span>
                  <span className={`inline-block text-[10px] font-bold text-white px-2 py-0.5 rounded-full ${zone.color}`}>
                    {zone.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Algorithm Emissions & Cost Comparison Bar Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-emerald-600" />
              <h3 className="font-bold text-slate-800 text-sm">Emissions Comparison across Solvers</h3>
            </div>
            <span className="text-[10px] bg-emerald-50 text-emerald-700 font-bold px-2.5 py-1 rounded-full">Lowest CO₂</span>
          </div>

          <div className="space-y-3.5">
            {emissionsData.map((item, i) => (
              <div key={i} className="text-xs">
                <div className="flex justify-between text-[11px] font-semibold text-slate-700 mb-1">
                  <span className={item.winner ? 'text-emerald-700 font-bold' : ''}>{item.algo}</span>
                  <span className="font-mono text-slate-800">{item.emissions} kg CO₂ ({item.cost.toFixed(0)} cost)</span>
                </div>
                <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${item.winner ? 'bg-emerald-500' : 'bg-slate-400'}`}
                    style={{ width: `${item.bar}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Main Algorithm Performance Comparison Table */}
      <AlgorithmComparisonTable />
    </div>
  );
}
