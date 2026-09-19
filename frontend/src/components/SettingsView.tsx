import { useState } from 'react';

export default function SettingsView() {
  const [alphaBounds, setAlphaBounds] = useState<[number, number]>([0.5, 1.0]);
  const [iterations, setIterations] = useState(100);
  const [population, setPopulation] = useState(100);
  const [useGls, setUseGls] = useState(true);
  const [useSwap, setUseSwap] = useState(true);

  const saveSettings = async () => {
    try {
      await fetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alpha_bounds: alphaBounds,
          max_iterations: iterations,
          population_size: population,
          use_gls: useGls,
          use_swap_star: useSwap
        })
      });
      alert('Settings saved!');
    } catch (e) {
      console.error(e);
      alert('Failed to save settings.');
    }
  };

  return (
    <div className="p-6 text-white h-full flex flex-col space-y-6 bg-slate-900 overflow-y-auto">
      <h2 className="text-2xl font-bold mb-4">Optimization Settings</h2>
      
      <div className="bg-slate-800 p-4 rounded-lg space-y-4">
        <h3 className="text-lg font-semibold border-b border-slate-700 pb-2">Algorithm Parameters</h3>
        
        <div>
          <label className="block text-sm font-medium mb-1">Max Iterations: {iterations}</label>
          <input type="range" min="10" max="500" value={iterations} onChange={(e) => setIterations(Number(e.target.value))} className="w-full" />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">Population Size: {population}</label>
          <input type="range" min="10" max="200" value={population} onChange={(e) => setPopulation(Number(e.target.value))} className="w-full" />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Alpha Bounds: {alphaBounds[0]} - {alphaBounds[1]}</label>
          <input type="range" min="0.1" max="1.0" step="0.1" value={alphaBounds[0]} onChange={(e) => setAlphaBounds([Number(e.target.value), alphaBounds[1]])} className="w-full" />
          <input type="range" min="0.1" max="2.0" step="0.1" value={alphaBounds[1]} onChange={(e) => setAlphaBounds([alphaBounds[0], Number(e.target.value)])} className="w-full mt-2" />
        </div>
      </div>

      <div className="bg-slate-800 p-4 rounded-lg space-y-4">
        <h3 className="text-lg font-semibold border-b border-slate-700 pb-2">Heuristics</h3>
        
        <label className="flex items-center space-x-3 cursor-pointer">
          <input type="checkbox" checked={useGls} onChange={(e) => setUseGls(e.target.checked)} className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 bg-slate-700 border-slate-600" />
          <span>Use Guided Local Search (GLS)</span>
        </label>
        
        <label className="flex items-center space-x-3 cursor-pointer">
          <input type="checkbox" checked={useSwap} onChange={(e) => setUseSwap(e.target.checked)} className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 bg-slate-700 border-slate-600" />
          <span>Use SWAP* Operator</span>
        </label>
      </div>

      <button onClick={saveSettings} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full md:w-auto self-start transition-colors">
        Save Settings
      </button>
    </div>
  );
}
