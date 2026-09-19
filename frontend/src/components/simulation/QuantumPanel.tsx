import React, { useState } from 'react';
import { Cpu, Activity, Flame, ShieldAlert, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

interface QuantumPanelProps {
  diversity: number;
  alpha: number;
  stagnation: number;
  maxStagnation?: number;
  levyActive: boolean;
}

export default function QuantumPanel({
  diversity = 0.28,
  alpha = 0.85,
  stagnation = 0,
  maxStagnation = 15,
  levyActive = false,
}: QuantumPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const getDiversityColor = (val: number) => {
    if (val > 0.25) return 'bg-emerald-500';
    if (val > 0.10) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  const getDiversityLabel = (val: number) => {
    if (val > 0.25) return 'High (Exploration)';
    if (val > 0.10) return 'Balanced';
    return 'Low (Convergence Risk)';
  };

  const diversityPercent = Math.min(Math.max(diversity * 100, 0), 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-slate-800 space-y-3">
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between cursor-pointer select-none border-b border-slate-100 pb-2.5"
      >
        <div className="flex items-center space-x-2">
          <Cpu className="h-4 w-4 text-blue-600" />
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-800">Quantum Telemetry Panel</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          {levyActive ? (
            <div className="flex items-center bg-amber-100 border border-amber-300 text-amber-800 text-[10px] px-2 py-0.5 rounded-full animate-pulse font-bold tracking-wider">
              <Sparkles className="h-3 w-3 mr-1 text-amber-600" />
              LÉVY ACTIVE
            </div>
          ) : (
            <div className="flex items-center bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded-full font-medium">
              <Flame className="h-3 w-3 mr-1 text-slate-400" />
              Normal State
            </div>
          )}
          {isOpen ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
        </div>
      </div>

      {isOpen && (
        <div className="grid grid-cols-2 gap-2.5 text-xs">
          <div className="col-span-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
            <div className="flex justify-between items-center mb-1">
              <span className="font-semibold text-slate-600 text-[11px] flex items-center">
                <Activity className="h-3.5 w-3.5 mr-1 text-blue-600" /> Swarm Diversity
              </span>
              <span className="font-mono font-bold text-slate-900">{diversity.toFixed(3)}</span>
            </div>
            <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${getDiversityColor(diversity)}`}
                style={{ width: `${diversityPercent}%` }}
              />
            </div>
            <div className="flex justify-between items-center mt-1 text-[10px] text-slate-500 font-mono">
              <span>{getDiversityLabel(diversity)}</span>
              <span>{diversityPercent.toFixed(1)}%</span>
            </div>
          </div>

          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 flex flex-col justify-between">
            <span className="text-slate-500 font-semibold text-[11px]">α Coefficient</span>
            <div className="flex items-baseline space-x-1.5 mt-1">
              <span className="text-lg font-mono font-bold text-blue-700">{alpha.toFixed(3)}</span>
              <span className="text-[10px] font-semibold text-blue-600">
                {alpha > 0.8 ? 'Expansion' : 'Contraction'}
              </span>
            </div>
          </div>

          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 flex flex-col justify-between">
            <span className="text-slate-500 font-semibold text-[11px] flex items-center">
              <ShieldAlert className="h-3.5 w-3.5 mr-1 text-amber-500" /> Stagnation
            </span>
            <div className="flex items-baseline space-x-1 mt-1">
              <span className={`text-lg font-mono font-bold ${stagnation > 10 ? 'text-rose-600' : 'text-slate-800'}`}>
                {stagnation}
              </span>
              <span className="text-slate-400 text-[10px] font-mono">/ {maxStagnation} iter</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
