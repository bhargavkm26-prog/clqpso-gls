import React from 'react';
import { Truck, PackageCheck, MapPin, X, ArrowRight } from 'lucide-react';

interface VehicleDrawerProps {
  selectedRouteIndex: number | null;
  routes: number[][];
  onClose: () => void;
  maxCapacity?: number;
}

export default function VehicleDrawer({
  selectedRouteIndex,
  routes,
  onClose,
  maxCapacity = 100,
}: VehicleDrawerProps) {
  if (selectedRouteIndex === null || !routes[selectedRouteIndex]) return null;

  const route = routes[selectedRouteIndex];
  const vehicleId = selectedRouteIndex + 1;
  
  const estimatedDemand = Math.min(route.length * 15, maxCapacity);
  const capacityPct = Math.min((estimatedDemand / maxCapacity) * 100, 100);

  return (
    <div className="bg-white border border-slate-200 shadow-xl rounded-xl p-4 text-xs space-y-3 relative">
      <button 
        onClick={onClose}
        className="absolute top-3 right-3 text-slate-400 hover:text-slate-600 rounded-full p-1 hover:bg-slate-100"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-center space-x-2 border-b border-slate-100 pb-2.5">
        <Truck className="h-5 w-5 text-blue-600" />
        <div>
          <h4 className="font-bold text-sm text-slate-800">Vehicle Route #{vehicleId} Details</h4>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">{route.length} Served Customers</span>
        </div>
      </div>

      <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
        <div className="flex justify-between items-center mb-1 font-semibold text-slate-600">
          <span className="flex items-center">
            <PackageCheck className="h-3.5 w-3.5 mr-1 text-emerald-600" /> Capacity Load
          </span>
          <span className="font-mono text-slate-800">{estimatedDemand} / {maxCapacity} units ({capacityPct.toFixed(0)}%)</span>
        </div>
        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
          <div 
            className={`h-full ${capacityPct > 90 ? 'bg-amber-500' : 'bg-blue-600'}`}
            style={{ width: `${capacityPct}%` }}
          />
        </div>
      </div>

      <div>
        <span className="font-bold text-slate-700 block mb-1.5 flex items-center">
          <MapPin className="h-3.5 w-3.5 mr-1 text-rose-500" /> Stop Sequence
        </span>
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60 font-mono text-[11px]">
          <span className="bg-black text-white px-2 py-0.5 rounded font-bold">Depot</span>
          <ArrowRight className="h-3 w-3 text-slate-400" />
          {route.map((cIdx, i) => (
            <React.Fragment key={cIdx}>
              <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-medium">C{cIdx + 1}</span>
              {i < route.length - 1 && <ArrowRight className="h-3 w-3 text-slate-300" />}
            </React.Fragment>
          ))}
          <ArrowRight className="h-3 w-3 text-slate-400" />
          <span className="bg-black text-white px-2 py-0.5 rounded font-bold">Depot</span>
        </div>
      </div>
    </div>
  );
}
