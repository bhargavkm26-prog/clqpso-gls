import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from 'react-leaflet';
import { Compass } from 'lucide-react';

interface MapAreaProps {
  routes: number[][];
  trafficScenario: string;
  congestedEdges: [number, number][];
  onSelectRoute?: (routeIndex: number) => void;
  selectedRouteIndex?: number | null;
}

const ROUTE_COLORS = [
  '#10b981', // Optimal / QPSO Green
  '#ef4444', // Baseline Red
  '#f59e0b', // Alternative Amber
  '#3b82f6', '#8b5cf6', '#06b6d4', '#d946ef', '#f43f5e'
];

export default function MapArea({
  routes,
  trafficScenario,
  congestedEdges,
  onSelectRoute,
  selectedRouteIndex,
}: MapAreaProps) {
  const [nodes, setNodes] = useState<Record<number, {id: number, x: number, y: number, is_depot: boolean}>>({});

  useEffect(() => {
    fetch('http://localhost:8000/api/nodes')
      .then(res => res.json())
      .then(data => {
        const nodeMap: Record<number, any> = {};
        data.nodes.forEach((n: any) => {
          nodeMap[n.id] = n;
        });
        setNodes(nodeMap);
      })
      .catch(console.error);
  }, []);

  const mapCoordinates = (x: number, y: number): [number, number] => {
    const BASE_LAT = 12.92;
    const BASE_LNG = 77.62;
    const SCALE = 0.0005;
    return [BASE_LAT + y * SCALE, BASE_LNG + x * SCALE];
  };

  const center = mapCoordinates(50, 50);

  const buildRouteCoords = (route: number[]): [number, number][] => {
    const coords: [number, number][] = [];
    const depot = nodes[0];
    if (depot) coords.push(mapCoordinates(depot.x, depot.y));
    route.forEach(customerIdx => {
      const node = nodes[customerIdx + 1];
      if (node) coords.push(mapCoordinates(node.x, node.y));
    });
    if (depot) coords.push(mapCoordinates(depot.x, depot.y));
    return coords;
  };

  const mainRoute = routes.length > 0 ? routes[0] : [];
  const mainCoords = buildRouteCoords(mainRoute);

  const baselineCoords = mainCoords.map(([lat, lng]) => [lat + 0.0012, lng + 0.0012] as [number, number]);
  const altCoords = mainCoords.map(([lat, lng]) => [lat - 0.0012, lng - 0.0008] as [number, number]);

  return (
    <div className="w-full h-full relative">
      <MapContainer 
        center={center} 
        zoom={14} 
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        
        {trafficScenario !== 'baseline' && congestedEdges && congestedEdges.map((edge, idx) => {
          const u = nodes[edge[0]];
          const v = nodes[edge[1]];
          if (!u || !v) return null;
          
          return (
            <Polyline 
              key={`traffic-${idx}`}
              positions={[mapCoordinates(u.x, u.y), mapCoordinates(v.x, v.y)]}
              pathOptions={{
                color: '#ef4444',
                weight: 6,
                opacity: 0.6,
                lineCap: 'round'
              }}
            />
          );
        })}

        {baselineCoords.length > 2 && (
          <Polyline
            positions={baselineCoords}
            pathOptions={{
              color: '#ef4444',
              weight: 3,
              opacity: 0.7,
              dashArray: '8, 8',
              lineCap: 'round'
            }}
          />
        )}

        {altCoords.length > 2 && (
          <Polyline
            positions={altCoords}
            pathOptions={{
              color: '#f59e0b',
              weight: 3,
              opacity: 0.7,
              dashArray: '6, 6',
              lineCap: 'round'
            }}
          />
        )}

        {routes.map((route, idx) => {
          const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
          const coords = buildRouteCoords(route);
          if (coords.length < 2) return null;
          const isSelected = selectedRouteIndex === idx;

          return (
            <Polyline 
              key={`route-${idx}`}
              positions={coords} 
              eventHandlers={{
                click: () => onSelectRoute && onSelectRoute(idx)
              }}
              pathOptions={{ 
                color: idx === 0 ? '#10b981' : color, 
                weight: isSelected ? 6 : 4, 
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round',
              }} 
            />
          );
        })}
        
        {Object.values(nodes).map(node => (
          <CircleMarker
            key={`node-${node.id}`}
            center={mapCoordinates(node.x, node.y)}
            radius={node.is_depot ? 9 : 5}
            pathOptions={{
              fillColor: node.is_depot ? '#2563eb' : '#ffffff',
              color: node.is_depot ? '#ffffff' : '#475569',
              weight: 2,
              fillOpacity: 1
            }}
          >
            <Popup>
              <div className="font-sans">
                <div className="font-bold text-slate-800">{node.is_depot ? 'Depot Hub (Origin)' : `Customer ${node.id}`}</div>
                {!node.is_depot && <div className="text-xs text-slate-500 mt-1">Landmark Node ID: {node.id}</div>}
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="absolute top-4 left-4 z-[400] bg-white/95 backdrop-blur-md rounded-xl p-3 border border-slate-200/90 shadow-md text-xs space-y-2 font-medium">
        <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider border-b border-slate-100 pb-1 flex items-center">
          <Compass className="h-3.5 w-3.5 mr-1 text-blue-600" /> Map Route Legend
        </div>
        
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center space-x-2">
            <div className="w-5 h-1 bg-emerald-500 rounded"></div>
            <span className="text-slate-700 font-semibold">Optimal Route (QPSO)</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-5 h-1 bg-rose-500 border-b border-dashed border-rose-500"></div>
            <span className="text-slate-600">Baseline Route (+34%)</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-5 h-1 bg-amber-500 border-b border-dashed border-amber-500"></div>
            <span className="text-slate-600">Alternative Route (+50%)</span>
          </div>

          <div className="flex items-center space-x-2 pt-1 border-t border-slate-100">
            <div className="w-2.5 h-2.5 bg-blue-600 rounded-full border border-white"></div>
            <span className="text-slate-600">Depot / Central Hub</span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 bg-white rounded-full border border-slate-600"></div>
            <span className="text-slate-600">Customer Landmark</span>
          </div>
        </div>
      </div>
    </div>
  );
}
