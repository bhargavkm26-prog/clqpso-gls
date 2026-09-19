import React from 'react';

const SCENARIOS = [
  { id: 'baseline', label: 'Baseline', color: 'bg-emerald-500' },
  { id: 'moderate', label: 'Moderate', color: 'bg-yellow-500' },
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
      <div className="flex justify-between items-center mb-3">
        <span className={`text-[10px] font-black px-2.5 py-1 rounded-md text-slate-900 tracking-wider uppercase ${SCENARIOS[currentIndex]?.color || 'bg-slate-500'} shadow-[0_0_10px_rgba(0,0,0,0.2)]`}>
          {SCENARIOS[currentIndex]?.label || 'Unknown'}
        </span>
      </div>
      
      <div className="relative w-full h-2 bg-slate-700 rounded-full mt-2">
        <input
          type="range"
          min="0"
          max="3"
          step="1"
          value={currentIndex}
          onChange={handleChange}
          className="absolute top-0 left-0 w-full h-2 opacity-0 cursor-pointer z-10"
        />
        {/* Custom Track Fill */}
        <div 
          className={`absolute top-0 left-0 h-2 rounded-full transition-all duration-300 ${SCENARIOS[currentIndex]?.color || 'bg-slate-500'}`}
          style={{ width: `${(currentIndex / 3) * 100}%` }}
        ></div>
        {/* Custom Thumb */}
        <div 
          className="absolute top-1/2 -mt-2 h-4 w-4 bg-white rounded-full shadow border-2 border-slate-800 transition-all duration-300 pointer-events-none"
          style={{ left: `calc(${(currentIndex / 3) * 100}% - 8px)` }}
        ></div>
      </div>
      
      <div className="flex justify-between text-[9px] text-slate-400 mt-3 px-1 font-bold uppercase tracking-widest">
        <span>Normal</span>
        <span>Rush Hr</span>
        <span>Accident</span>
        <span>Clear</span>
      </div>
    </div>
  );
}
