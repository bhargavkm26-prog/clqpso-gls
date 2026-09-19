import { useState, useEffect, useRef } from 'react';
import { Play, Square, RefreshCcw, Activity, Truck, Map as MapIcon, TrendingDown } from 'lucide-react';
import MapArea from './MapArea';
import MetricsSidebar from './MetricsSidebar';
import ConvergenceChart from './ConvergenceChart';
import TrafficSlider from './TrafficSlider';
import AlgorithmRace from './AlgorithmRace';

export default function Dashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [bestFitness, setBestFitness] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [convergenceData, setConvergenceData] = useState<{iteration: number, cost: number}[]>([]);
  const [routes, setRoutes] = useState<number[][]>([]);
  const [trafficScenario, setTrafficScenario] = useState('baseline');
  const [congestedEdges, setCongestedEdges] = useState<[number, number][]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/api/ws');
    
    ws.onopen = () => {
      console.log('Connected to optimization server');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'iteration_update') {
        setIteration(data.iteration);
        setBestFitness(data.best_fitness);
        if (data.elapsed_ms !== undefined) {
          setElapsedMs(data.elapsed_ms);
        }
        setRoutes(data.routes);
        
        setConvergenceData(prev => {
          const newData = [...prev, { iteration: data.iteration, cost: data.best_fitness }];
          // Keep last 100 points
          if (newData.length > 100) return newData.slice(newData.length - 100);
          return newData;
        });
      } else if (data.type === 'status') {
        setIsRunning(data.is_running);
      } else if (data.type === 'traffic_update') {
        setTrafficScenario(data.scenario_id);
        if (data.congested_edges) {
          setCongestedEdges(data.congested_edges);
        } else {
          setCongestedEdges([]);
        }
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };
    
    ws.onclose = () => {
      console.log('Disconnected from optimization server');
      setIsRunning(false);
    };
    
    wsRef.current = ws;
    
    // Check initial status
    fetch('http://localhost:8000/api/status')
      .then(res => res.json())
      .then(data => {
        setIsRunning(data.is_running);
        if (data.scenario_id) setTrafficScenario(data.scenario_id);
      })
      .catch(console.error);
      
    return () => {
      ws.close();
    };
  }, []);

  const handleStart = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ iterations: 1000, scenario_id: trafficScenario })
      });
      if (res.ok) {
        setIsRunning(true);
        setConvergenceData([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/stop', { method: 'POST' });
      if (res.ok) setIsRunning(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleScenarioChange = async (scenario: string) => {
    try {
      const res = await fetch('http://localhost:8000/api/traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenario })
      });
      if (res.ok) {
        setTrafficScenario(scenario);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden text-slate-800 font-sans">
      
      {/* Sidebar - Dark Professional Theme */}
      <div className="w-80 bg-slate-900 flex flex-col shadow-2xl z-20 shrink-0">
        <div className="p-6 border-b border-slate-800 flex items-center space-x-4 bg-slate-900/50">
          <div className="bg-indigo-500/20 p-2 rounded-lg border border-indigo-500/30">
            <Activity className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight text-white">CLQPSO<span className="text-indigo-400">-GLS</span></h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold mt-0.5">Quantum VRP Optimizer</p>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <MetricsSidebar 
            iteration={iteration} 
            bestFitness={bestFitness} 
            vehicleCount={routes.length} 
            elapsedMs={elapsedMs}
          />
          
          <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
            <h3 className="text-xs font-semibold text-slate-300 mb-4 flex items-center uppercase tracking-wider">
              <MapIcon className="h-4 w-4 mr-2 text-blue-400" /> Traffic Scenario
            </h3>
            <TrafficSlider scenario={trafficScenario} onChange={handleScenarioChange} />
          </div>
          
          <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
             <h3 className="text-xs font-semibold text-slate-300 mb-4 flex items-center uppercase tracking-wider">
              <Truck className="h-4 w-4 mr-2 text-emerald-400" /> Controls
            </h3>
            <div className="flex space-x-3">
              {!isRunning ? (
                <button 
                  onClick={handleStart}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 flex justify-center items-center font-semibold shadow-[0_0_15px_rgba(79,70,229,0.3)] transition-all duration-200 border border-indigo-500"
                >
                  <Play className="h-4 w-4 mr-2" fill="currentColor" /> START
                </button>
              ) : (
                <button 
                  onClick={handleStop}
                  className="flex-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg py-2.5 px-4 flex justify-center items-center font-semibold shadow-[0_0_15px_rgba(225,29,72,0.3)] transition-all duration-200 border border-rose-500"
                >
                  <Square className="h-4 w-4 mr-2" fill="currentColor" /> STOP
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative min-w-0">
        
        {/* Top Status Pill overlaying map */}
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-white/95 backdrop-blur-md rounded-full shadow-lg border border-slate-200/60 px-5 py-2.5 flex items-center space-x-6">
           <div className="flex items-center">
             <div className="relative flex h-3 w-3 mr-3">
               {isRunning && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
               <span className={`relative inline-flex rounded-full h-3 w-3 ${isRunning ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
             </div>
             <span className="text-sm font-bold text-slate-700 uppercase tracking-wide">{isRunning ? 'Optimizer Running' : 'System Idle'}</span>
           </div>
           {isRunning && (
             <div className="flex items-center pl-6 border-l border-slate-200">
                <RefreshCcw className="h-4 w-4 text-indigo-500 mr-2 animate-spin-slow" />
                <span className="text-sm font-bold text-indigo-700 font-mono tracking-tight">ITERATION {iteration}</span>
             </div>
           )}
        </div>
        
        <div className="flex-1 relative z-0">
          <MapArea routes={routes} trafficScenario={trafficScenario} congestedEdges={congestedEdges} />
        </div>
        
        {/* Bottom panel: Charts */}
        <div className="h-[24rem] bg-white border-t border-slate-200 p-5 shadow-[0_-10px_30px_-15px_rgba(0,0,0,0.1)] z-10 overflow-hidden flex flex-col xl:flex-row gap-6 relative">
           
           <div className="flex-1 flex flex-col h-full bg-slate-50/50 rounded-xl border border-slate-100 p-4">
             <div className="flex items-center justify-between mb-3 shrink-0">
               <h3 className="text-sm font-bold text-slate-800 flex items-center uppercase tracking-wider">
                  <TrendingDown className="h-4 w-4 mr-2 text-indigo-600" /> Convergence Analysis
               </h3>
               {bestFitness && <span className="text-xs font-semibold text-slate-500 font-mono">Current: {bestFitness.toFixed(2)}</span>}
             </div>
             <div className="flex-1 min-h-0 relative">
                <ConvergenceChart data={convergenceData} />
             </div>
           </div>

           <div className="flex-1 flex flex-col h-full bg-slate-50/50 rounded-xl border border-slate-100 p-4 xl:max-w-[45%]">
             <AlgorithmRace />
           </div>

        </div>
      </div>
    </div>
  );
}
