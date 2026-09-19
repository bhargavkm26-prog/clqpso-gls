import React from 'react';
import { Leaf, Fuel, Clock } from 'lucide-react';

interface ImpactPanelProps {
  bestFitness: number | null;
  vehicleCount: number;
}

export default function ImpactPanel({ bestFitness }: ImpactPanelProps) {
  const baseCost = bestFitness ? bestFitness * 1.30 : 1000;
  const distanceSavedKm = bestFitness ? (baseCost - bestFitness) * 0.05 : 18.5;
  
  const co2SavedKg = (distanceSavedKm * 0.21).toFixed(1);
  const fuelSavedL = (distanceSavedKm * 0.09).toFixed(1);
  const driverHoursSaved = (distanceSavedKm / 25.0).toFixed(1);

  return (
    <div className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white rounded-xl p-4 border border-indigo-900/60 shadow-md space-y-3">
      <div className="flex items-center space-x-2 border-b border-indigo-900/80 pb-2">
        <Leaf className="h-4 w-4 text-emerald-400" />
        <h3 className="font-bold text-xs uppercase tracking-wider text-emerald-200">Smart-City Logistics Impact</h3>
      </div>

      <div className="grid grid-cols-3 gap-2.5 text-center">
        <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700/60">
          <div className="flex items-center justify-center text-emerald-400 mb-1">
            <Leaf className="h-3.5 w-3.5 mr-1" />
            <span className="text-[10px] font-semibold text-slate-400 uppercase">CO₂ Avoided</span>
          </div>
          <div className="text-base font-bold font-mono text-emerald-300">{co2SavedKg} <span className="text-[10px] text-slate-400">kg</span></div>
        </div>

        <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700/60">
          <div className="flex items-center justify-center text-amber-400 mb-1">
            <Fuel className="h-3.5 w-3.5 mr-1" />
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Fuel Saved</span>
          </div>
          <div className="text-base font-bold font-mono text-amber-300">{fuelSavedL} <span className="text-[10px] text-slate-400">L</span></div>
        </div>

        <div className="bg-slate-800/80 p-2.5 rounded-lg border border-slate-700/60">
          <div className="flex items-center justify-center text-blue-400 mb-1">
            <Clock className="h-3.5 w-3.5 mr-1" />
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Time Saved</span>
          </div>
          <div className="text-base font-bold font-mono text-blue-300">{driverHoursSaved} <span className="text-[10px] text-slate-400">hrs</span></div>
        </div>
      </div>
    </div>
  );
}
