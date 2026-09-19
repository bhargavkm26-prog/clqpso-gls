import { useState, useEffect, useRef } from 'react';
import { Play, Square, RefreshCcw, Activity, Navigation, Map as MapIcon, BarChart2, Award, Cpu, Shield, ArrowRight, Layers } from 'lucide-react';
import MapArea from './simulation/MapArea';
import MetricsSidebar from './simulation/MetricsSidebar';
import TrafficSlider from './simulation/TrafficSlider';
import QuantumPanel from './simulation/QuantumPanel';
import ExplanationCard from './simulation/ExplanationCard';
import VehicleDrawer from './simulation/VehicleDrawer';
import AnalyticsDashboard from './analytics/AnalyticsDashboard';
import CompareView from './compare/CompareView';

export default function Dashboard() {
  const [activeNav, setActiveNav] = useState<'simulation' | 'analytics' | 'compare'>('simulation');

  // Optimization state
  const [isRunning, setIsRunning] = useState(false);
  const [iteration, setIteration] = useState(0);
  const [bestFitness, setBestFitness] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [convergenceData, setConvergenceData] = useState<{iteration: number, cost: number}[]>([]);
  const [routes, setRoutes] = useState<number[][]>([]);
  const [trafficScenario, setTrafficScenario] = useState('baseline');
  const [congestedEdges, setCongestedEdges] = useState<[number, number][]>([]);

  // From / To Dropdown Selection
  const [fromDepot, setFromDepot] = useState('Central Hub (Depot 0)');
  const [toDestination, setToDestination] = useState('All Customers (Indiranagar / Koramangala)');

  // Quantum metrics state
  const [quantumMetrics, setQuantumMetrics] = useState({
    diversity: 0.28,
    alpha: 0.85,
    stagnation: 0,
    levyActive: false
  });

  // UI Drawer & Rationale Card State
  const [selectedRouteIndex, setSelectedRouteIndex] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
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

        if (data.quantum_metrics) {
          setQuantumMetrics({
            diversity: data.quantum_metrics.diversity ?? 0.25,
            alpha: data.quantum_metrics.alpha ?? 0.85,
            stagnation: data.quantum_metrics.stagnation ?? 0,
            levyActive: !!data.quantum_metrics.levy_active
          });
        }
        
        setConvergenceData(prev => {
          const newData = [...prev, { iteration: data.iteration, cost: data.best_fitness }];
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
      
      {/* Left Navigation Sidebar (Fixed, Light Theme) */}
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm z-30 shrink-0">
        
        {/* Logo & Title */}
        <div className="p-4 border-b border-slate-100 flex items-center space-x-3 bg-white">
          <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-200">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-base text-slate-900 tracking-tight">QPSO Logistics</h1>
            <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Bangalore Traffic System</p>
          </div>
        </div>
        
        {/* Navigation Items */}
        <div className="flex-1 py-4 space-y-1 px-3">
          <button
            onClick={() => setActiveNav('simulation')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeNav === 'simulation'
                ? 'bg-blue-50 border-l-4 border-blue-600 text-blue-700 shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Navigation className={`h-4 w-4 ${activeNav === 'simulation' ? 'text-blue-600' : 'text-slate-400'}`} />
            <span>Live Simulation</span>
          </button>

          <button
            onClick={() => setActiveNav('analytics')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeNav === 'analytics'
                ? 'bg-blue-50 border-l-4 border-blue-600 text-blue-700 shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <BarChart2 className={`h-4 w-4 ${activeNav === 'analytics' ? 'text-blue-600' : 'text-slate-400'}`} />
            <span>Analytics Dashboard</span>
          </button>

          <button
            onClick={() => setActiveNav('compare')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeNav === 'compare'
                ? 'bg-blue-50 border-l-4 border-blue-600 text-blue-700 shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Award className={`h-4 w-4 ${activeNav === 'compare' ? 'text-blue-600' : 'text-slate-400'}`} />
            <span>Compare Algorithms</span>
          </button>
        </div>

        {/* Footer Tagline */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-400 text-center font-medium">
          Smarter Roads, Greener Tomorrow
        </div>
      </div>
      
      {/* Main Content View */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Top Header Bar */}
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between z-20 shadow-sm shrink-0">
          <div>
            <h2 className="font-bold text-slate-800 text-base">
              {activeNav === 'simulation' ? 'Live Traffic & Route Simulation' : activeNav === 'analytics' ? 'Network Analytics Dashboard' : 'Algorithm Performance Comparison'}
            </h2>
            <p className="text-xs text-slate-500">
              {activeNav === 'simulation' ? 'Bangalore Urban Logistics Network Optimization' : activeNav === 'analytics' ? 'Real-time Traffic Volume, CO₂ & Network Efficiency' : 'Benchmark Evaluation vs Baselines (Phase 9)'}
            </p>
          </div>

          {/* Top Bar Controls for Simulation View */}
          {activeNav === 'simulation' && (
            <div className="flex items-center space-x-3">
              {/* From Input Pill */}
              <div className="bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 flex items-center text-xs text-slate-700">
                <span className="text-slate-400 mr-1.5 font-semibold shrink-0">From:</span>
                <input 
                  type="text"
                  value={fromDepot} 
                  onChange={(e) => setFromDepot(e.target.value)}
                  placeholder="Enter origin location..."
                  className="bg-transparent font-bold outline-none text-slate-800 w-48"
                />
              </div>

              {/* To Input Pill */}
              <div className="bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 flex items-center text-xs text-slate-700">
                <span className="text-slate-400 mr-1.5 font-semibold shrink-0">To:</span>
                <input 
                  type="text"
                  value={toDestination} 
                  onChange={(e) => setToDestination(e.target.value)}
                  placeholder="Enter destination / zone..."
                  className="bg-transparent font-bold outline-none text-slate-800 w-56"
                />
              </div>

              {/* Primary Green Run Optimization Button */}
              {!isRunning ? (
                <button
                  onClick={handleStart}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 px-4 flex items-center font-bold text-xs shadow-md shadow-emerald-200 transition-all"
                >
                  <Play className="h-3.5 w-3.5 mr-1.5" fill="currentColor" /> Run Optimization
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="bg-rose-600 hover:bg-rose-700 text-white rounded-lg py-2 px-4 flex items-center font-bold text-xs shadow-md shadow-rose-200 transition-all"
                >
                  <Square className="h-3.5 w-3.5 mr-1.5" fill="currentColor" /> Stop Engine
                </button>
              )}
            </div>
          )}
        </div>

        {/* View Content Renderer */}
        {activeNav === 'simulation' ? (
          <div className="flex-1 flex overflow-hidden">
            
            {/* Map Area */}
            <div className="flex-1 relative z-0">
              <MapArea 
                routes={routes} 
                trafficScenario={trafficScenario} 
                congestedEdges={congestedEdges}
                onSelectRoute={(idx) => setSelectedRouteIndex(idx)}
                selectedRouteIndex={selectedRouteIndex}
              />

              {/* Rationale & Drawer Floating Overlays */}
              {(showExplanation || selectedRouteIndex !== null) && (
                <div className="absolute bottom-4 left-4 right-4 z-[450] flex flex-col md:flex-row gap-3 pointer-events-none">
                  {showExplanation && (
                    <div className="flex-1 pointer-events-auto">
                      <ExplanationCard
                        selectedRouteIndex={selectedRouteIndex}
                        routeStops={selectedRouteIndex !== null ? routes[selectedRouteIndex] : null}
                        trafficScenario={trafficScenario}
                      />
                    </div>
                  )}
                  {selectedRouteIndex !== null && (
                    <div className="w-96 pointer-events-auto">
                      <VehicleDrawer
                        selectedRouteIndex={selectedRouteIndex}
                        routes={routes}
                        onClose={() => setSelectedRouteIndex(null)}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Panel: Route Summary & Quantum Telemetry */}
            <div className="w-96 bg-slate-50 border-l border-slate-200 p-4 overflow-y-auto space-y-4 shrink-0 shadow-inner">
              <MetricsSidebar
                iteration={iteration}
                bestFitness={bestFitness}
                vehicleCount={routes.length}
                elapsedMs={elapsedMs}
                onOpenExplanation={() => setShowExplanation(!showExplanation)}
              />

              <QuantumPanel
                diversity={quantumMetrics.diversity}
                alpha={quantumMetrics.alpha}
                stagnation={quantumMetrics.stagnation}
                levyActive={quantumMetrics.levyActive}
              />

              <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 mb-2 flex items-center uppercase tracking-wider">
                  <MapIcon className="h-3.5 w-3.5 mr-1.5 text-blue-600" /> Traffic Scenario Controller
                </h3>
                <TrafficSlider scenario={trafficScenario} onChange={handleScenarioChange} />
              </div>
            </div>

          </div>
        ) : activeNav === 'analytics' ? (
          <div className="flex-1 overflow-y-auto">
            <AnalyticsDashboard />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <CompareView />
          </div>
        )}

      </div>
    </div>
  );
}
