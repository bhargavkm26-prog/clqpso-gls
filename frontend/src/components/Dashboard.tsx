import { useState, useEffect, useRef } from 'react';
import { Play, Square, RefreshCcw, Activity, Truck, Map as MapIcon, Clock, TrendingDown } from 'lucide-react';
import MapArea from './MapArea';
import MetricsSidebar from './MetricsSidebar';
import ConvergenceChart from './ConvergenceChart';
import TrafficSlider from './TrafficSlider';
import AlgorithmRace from './AlgorithmRace';

export default function Dashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [bestFitness, setBestFitness] = useState<number | null>(null);
  const [convergenceData, setConvergenceData] = useState<{iteration: number, cost: number}[]>([]);
  const [routes, setRoutes] = useState<number[][]>([]);
  const [trafficScenario, setTrafficScenario] = useState('baseline');
  
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
    <div className="flex h-screen bg-slate-50 overflow-hidden text-slate-800 font-sans">
      
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col shadow-sm z-10">
        <div className="p-5 border-b border-slate-100 flex items-center space-x-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
          <Activity className="h-6 w-6 text-blue-200" />
          <div>
            <h1 className="font-bold text-lg tracking-tight">CLQPSO-GLS</h1>
            <p className="text-xs text-blue-200 uppercase tracking-wider font-semibold">Quantum VRP Optimizer</p>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          <MetricsSidebar 
            iteration={iteration} 
            bestFitness={bestFitness} 
            vehicleCount={routes.length} 
          />
          
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <h3 className="text-sm font-semibold text-slate-500 mb-3 flex items-center uppercase tracking-wider">
              <MapIcon className="h-4 w-4 mr-2" /> Traffic Scenario
            </h3>
            <TrafficSlider scenario={trafficScenario} onChange={handleScenarioChange} />
          </div>
          
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
             <h3 className="text-sm font-semibold text-slate-500 mb-3 flex items-center uppercase tracking-wider">
              <Truck className="h-4 w-4 mr-2" /> Controls
            </h3>
            <div className="flex space-x-2">
              {!isRunning ? (
                <button 
                  onClick={handleStart}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2.5 px-4 flex justify-center items-center font-medium shadow-sm shadow-blue-200 transition-colors"
                >
                  <Play className="h-4 w-4 mr-2" fill="currentColor" /> Start
                </button>
              ) : (
                <button 
                  onClick={handleStop}
                  className="flex-1 bg-rose-500 hover:bg-rose-600 text-white rounded-lg py-2.5 px-4 flex justify-center items-center font-medium shadow-sm shadow-rose-200 transition-colors"
                >
                  <Square className="h-4 w-4 mr-2" fill="currentColor" /> Stop
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        <div className="absolute top-4 left-4 z-20 bg-white/90 backdrop-blur rounded-lg shadow border border-slate-200 p-3 flex items-center space-x-4">
           <div className="flex items-center">
             <div className={`h-2.5 w-2.5 rounded-full mr-2 ${isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`}></div>
             <span className="text-sm font-medium text-slate-600">{isRunning ? 'Optimizer Running' : 'Idle'}</span>
           </div>
           {isRunning && (
             <div className="flex items-center pl-4 border-l border-slate-200">
                <RefreshCcw className="h-4 w-4 text-blue-500 mr-2 animate-spin-slow" />
                <span className="text-sm font-semibold text-blue-700">Iteration {iteration}</span>
             </div>
           )}
        </div>
        
        <div className="flex-1 relative z-0">
          <MapArea routes={routes} trafficScenario={trafficScenario} />
        </div>
        
        {/* Bottom panel: Charts */}
        <div className="h-[26rem] bg-white border-t border-slate-200 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10 overflow-hidden flex flex-col md:flex-row gap-6">
           
           <div className="flex-1 flex flex-col h-full">
             <h3 className="text-sm font-bold text-slate-700 mb-3 flex items-center shrink-0">
                <TrendingDown className="h-4 w-4 mr-2 text-indigo-500" /> Real-time Convergence
             </h3>
             <div className="flex-1 min-h-0">
                <ConvergenceChart data={convergenceData} />
             </div>
           </div>

           <div className="flex-1 flex flex-col h-full pl-6 border-l border-slate-200">
             <AlgorithmRace />
           </div>

        </div>
      </div>
    </div>
  );
}
