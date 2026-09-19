import { useState, useEffect, useRef } from 'react';
import { Play, Square, Settings as SettingsIcon, LayoutDashboard, BarChart2, CheckCircle } from 'lucide-react';
import MapArea from './MapArea';
import MetricsSidebar from './MetricsSidebar';
import ConvergenceChart from './ConvergenceChart';
import TrafficSlider from './TrafficSlider';
import SettingsView from './SettingsView';
import HistoryView from './HistoryView';
import MetricsView from './MetricsView';
import StatusPopup from './StatusPopup';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('vrp');
  const [isRunning, setIsRunning] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [bestFitness, setBestFitness] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [convergenceData, setConvergenceData] = useState<{iteration: number, cost: number}[]>([]);
  const [routes, setRoutes] = useState<number[][]>([]);
  const [trafficScenario, setTrafficScenario] = useState('baseline');
  const [congestedEdges, setCongestedEdges] = useState<[number, number][]>([]);
  const [nodes, setNodes] = useState({});
  
  const [interactionMode, setInteractionMode] = useState<'view' | 'depot' | 'customer'>('view');
  const [depot, setDepot] = useState<[number, number]>([12.9716, 77.5946]);
  const [customers, setCustomers] = useState<[number, number][]>([]);
  const vehicleCapacity = 100;
  const maxVehicles = 25;
  const [errorMsg, setErrorMsg] = useState('');
  const [statusLogs, setStatusLogs] = useState<string[]>([]);
  const [isSetupComplete, setIsSetupComplete] = useState(false);
  const [benchmarkData, setBenchmarkData] = useState<any[] | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Fetch nodes
    fetch('http://localhost:8000/api/nodes')
      .then(r => r.json())
      .then(d => {
        const nodeMap: Record<number, any> = {};
        d.nodes.forEach((n: any) => nodeMap[n.id] = n);
        setNodes(nodeMap);
      })
      .catch(e => console.error("Error fetching nodes:", e));

    let ws: WebSocket;
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    
    const connectWS = () => {
      ws = new WebSocket('ws://localhost:8000/api/ws');
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('Connected to Optimization Engine');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'iteration_update') {
          setIteration(data.iteration);
          setBestFitness(data.best_fitness);
          setRoutes(data.routes || []);
          if (data.elapsed_ms) setElapsedMs(data.elapsed_ms);
          setConvergenceData(prev => {
            // Keep last 50 points
            const newData = [...prev, { iteration: data.iteration, cost: data.best_fitness }];
            return newData.length > 50 ? newData.slice(newData.length - 50) : newData;
          });
        } else if (data.type === 'status') {
          setIsRunning(data.is_running);
        } else if (data.type === 'traffic_update') {
          setCongestedEdges(data.congested_edges || []);
        } else if (data.type === 'log') {
          // If a log arrives when setup is complete, it means we're in the live benchmark phase
          if (isSetupComplete) setIsSetupComplete(false);
          setStatusLogs(prev => [...prev, data.message]);
        } else if (data.type === 'setup_complete') {
          setIsSetupComplete(true);
        } else if (data.type === 'live_benchmark') {
          setBenchmarkData(data.results);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 2s...');
        reconnectTimeout = setTimeout(connectWS, 2000);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    };

    connectWS();
    
    return () => {
      clearTimeout(reconnectTimeout);
      if (ws.readyState === WebSocket.OPEN) {
        // Prevent reconnect loop on unmount by removing onclose
        ws.onclose = null; 
        ws.close();
      }
    };
  }, []);

  const handleStart = async () => {
    if (customers.length === 0 && !depot) {
      alert("Please add at least one customer and set a depot to start optimization.");
      return;
    }
    
    // Optimistic UI update for instant feedback
    setErrorMsg('');
    setIsRunning(true);
    setConvergenceData([]);
    setStatusLogs(['Initiating Optimization Sequence...']);
    setIsSetupComplete(false);
    setBenchmarkData(null); // Clear previous benchmark data
    
    try {
      const res = await fetch('http://localhost:8000/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          depot: depot,
          customers: customers,
          vehicle_capacity: vehicleCapacity,
          max_vehicles: maxVehicles,
          scenario_id: trafficScenario
        })
      });
      if (!res.ok) {
        setIsRunning(false);
        const body = await res.json();
        setErrorMsg(body.detail || "Failed to start optimization");
      }
    } catch (e) {
      console.error(e);
      setIsRunning(false);
      setErrorMsg("Failed to connect to backend");
    }
  };

  const handleStop = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/stop', { method: 'POST' });
      if (res.ok) {
        setIsRunning(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleTrafficChange = async (scenario: string) => {
    setTrafficScenario(scenario);
    try {
      const res = await fetch('http://localhost:8000/api/traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenario })
      });
      if (!res.ok) console.error("Failed to update traffic");
    } catch (e) {
      console.error(e);
    }
  };

  const handleMapClick = (lat: number, lng: number) => {
    if (interactionMode === 'depot') {
      setDepot([lat, lng]);
      setInteractionMode('view');
    } else if (interactionMode === 'customer') {
      setCustomers([...customers, [lat, lng]]);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      
      {/* Sidebar Nav */}
      <div className="w-16 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-4 space-y-6">
        <button onClick={() => setActiveTab('vrp')} className={`p-3 rounded-xl transition-colors ${activeTab === 'vrp' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`} title="VRP Optimization">
          <LayoutDashboard size={24} />
        </button>
        <button onClick={() => setActiveTab('settings')} className={`p-3 rounded-xl transition-colors ${activeTab === 'settings' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`} title="Settings">
          <SettingsIcon size={24} />
        </button>
        <button onClick={() => setActiveTab('benchmarks')} className={`p-3 rounded-xl transition-colors ${activeTab === 'benchmarks' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`} title="Benchmarks">
          <CheckCircle size={24} />
        </button>
        <button onClick={() => setActiveTab('scaling')} className={`p-3 rounded-xl transition-colors ${activeTab === 'scaling' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`} title="Scaling Metrics">
          <BarChart2 size={24} />
        </button>
      </div>

      <div className="flex-1 flex flex-col min-w-0 h-full">
        <header className="h-16 bg-slate-900/50 backdrop-blur-md border-b border-slate-800 flex items-center px-6 shrink-0">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            CLQPSO-GLS Optimization Engine
          </h1>
          {activeTab === 'vrp' && (
            <div className="ml-auto flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                isRunning 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {isRunning ? 'OPTIMIZING' : 'IDLE'}
              </span>
            </div>
          )}
        </header>
        
        {activeTab === 'vrp' && (
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col min-w-0">
              
              {/* Interaction Bar */}
              <div className="bg-slate-800/80 p-2 border-b border-slate-700 flex items-center space-x-4">
                <button 
                  onClick={() => setInteractionMode(interactionMode === 'depot' ? 'view' : 'depot')}
                  className={`px-3 py-1 text-sm rounded ${interactionMode === 'depot' ? 'bg-red-600 text-white' : 'bg-slate-700 hover:bg-slate-600'}`}
                >
                  Set Depot
                </button>
                <button 
                  onClick={() => setInteractionMode(interactionMode === 'customer' ? 'view' : 'customer')}
                  className={`px-3 py-1 text-sm rounded ${interactionMode === 'customer' ? 'bg-blue-600 text-white' : 'bg-slate-700 hover:bg-slate-600'}`}
                >
                  Add Stops
                </button>
                <div className="flex-1"></div>
                {errorMsg && <span className="text-red-400 text-sm font-semibold">{errorMsg}</span>}
                <button
                  onClick={isRunning ? handleStop : handleStart}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all active:scale-95 ${
                    isRunning 
                      ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/50' 
                      : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-900/20'
                  }`}
                >
                  {isRunning ? <><Square size={18} /><span>Stop</span></> : <><Play size={18} /><span>Optimize</span></>}
                </button>
              </div>

              {/* Map Area */}
              <div className="flex-1 relative z-0">
                <MapArea 
                  nodes={nodes} 
                  routes={routes} 
                  trafficEdges={congestedEdges} 
                  depot={depot}
                  customers={customers}
                  onMapClick={handleMapClick}
                  interactionMode={interactionMode}
                />
                
                {/* Overlays inside Map Container */}
                <div className="absolute top-4 right-4 z-[400] w-72 space-y-4 pointer-events-none">
                  <div className="bg-slate-900/80 backdrop-blur-md p-4 rounded-xl border border-slate-700 pointer-events-auto shadow-2xl">
                    <TrafficSlider scenario={trafficScenario} onChange={handleTrafficChange} />
                  </div>
                </div>
                
                {/* Status Popup Overlay */}
                <StatusPopup logs={statusLogs} isComplete={isSetupComplete} />
              </div>
              
              {/* Bottom Panel */}
              <div className="h-48 bg-slate-900 border-t border-slate-800 p-4 shrink-0 overflow-hidden">
                <div className="w-full h-full bg-slate-800/50 rounded-lg p-3">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Convergence History</h3>
                  <ConvergenceChart data={convergenceData} />
                </div>
              </div>
            </div>
            
            {/* Right Sidebar */}
            <div className="w-80 bg-slate-900 border-l border-slate-800 shrink-0">
              <MetricsSidebar 
                iteration={iteration} 
                bestFitness={bestFitness} 
                vehicleCount={routes.length} 
                elapsedMs={elapsedMs}
                benchmarkData={benchmarkData}
              />
            </div>
          </div>
        )}

        {activeTab === 'settings' && <SettingsView />}
        {activeTab === 'benchmarks' && <HistoryView />}
        {activeTab === 'scaling' && <MetricsView />}
      </div>
    </div>
  );
}
