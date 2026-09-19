import React from 'react';

const SCENARIOS = [
  { id: 'baseline', label: 'Baseline', color: 'bg-emerald-500' },
  { id: 'moderate_traffic', label: 'Moderate', color: 'bg-yellow-500' },
  { id: 'disruption', label: 'Disruption', color: 'bg-red-500' },
  { id: 'recovery', label: 'Recovery', color: 'bg-blue-500' }
];

interface TrafficSliderProps {
  scenario: string;
  onChange: (scenarioId: string) => void;
}

export default function TrafficSlider({ scenario, onChange }: TrafficSliderProps) {
  const currentIndex = SCENARIOS.findIndex(s => s.id === scenario) || 0;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newIndex = parseInt(e.target.value, 10);
    onChange(SCENARIOS[newIndex].id);
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-end mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Traffic Level
        </span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded text-white ${SCENARIOS[currentIndex]?.color || 'bg-slate-500'}`}>
          {SCENARIOS[currentIndex]?.label || 'Unknown'}
        </span>
      </div>
      
      <input
        type="range"
        min="0"
        max="3"
        step="1"
        value={currentIndex}
        onChange={handleChange}
        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
      
      <div className="flex justify-between text-[10px] text-slate-400 mt-2 px-1 font-medium">
        <span>Normal</span>
        <span>Rush Hr</span>
        <span>Accident</span>
        <span>Clear</span>
      </div>
    </div>
  );
}
