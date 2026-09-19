import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from 'react-leaflet';

interface MapAreaProps {
  routes: number[][];
  trafficScenario: string;
  congestedEdges: [number, number][];
}

// Pastel colors for routes
const ROUTE_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981', 
  '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#d946ef', '#f43f5e'
];

export default function MapArea({ routes, trafficScenario, congestedEdges }: MapAreaProps) {
  const [nodes, setNodes] = useState<Record<number, {id: number, x: number, y: number, is_depot: boolean}>>({});
  
  useEffect(() => {
    // Fetch nodes for visualization
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

  // Map 0-100 coordinates to actual lat/lng in Bangalore (Koramangala approx)
  const mapCoordinates = (x: number, y: number): [number, number] => {
    const BASE_LAT = 12.92;
    const BASE_LNG = 77.62;
    const SCALE = 0.0005; // ~50m per unit
    return [BASE_LAT + y * SCALE, BASE_LNG + x * SCALE];
  };

  const center = mapCoordinates(50, 50);

  return (
    <MapContainer 
      center={center} 
      zoom={14} 
      style={{ height: '100%', width: '100%' }}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* Traffic Overlay (Congested Edges) */}
      {trafficScenario !== 'baseline' && congestedEdges && congestedEdges.map((edge, idx) => {
        const u = nodes[edge[0]];
        const v = nodes[edge[1]];
        if (!u || !v) return null;
        
        return (
          <Polyline 
            key={`traffic-${idx}`}
            positions={[mapCoordinates(u.x, u.y), mapCoordinates(v.x, v.y)]}
            pathOptions={{
              color: '#ef4444', // red
              weight: 6,
              opacity: 0.5,
              lineCap: 'round'
            }}
          />
        );
      })}
      
      {/* Routes */}
      {routes.map((route, idx) => {
        const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
        
        // Build coordinates array (Depot -> Customers -> Depot)
        const coords: [number, number][] = [];
        const depot = nodes[0];
        
        if (depot) {
          coords.push(mapCoordinates(depot.x, depot.y));
        }
        
        route.forEach(customerIdx => {
          // customerIdx is 0-based in route, but nodes have depot at 0 and customers at 1..n
          const node = nodes[customerIdx + 1];
          if (node) {
            coords.push(mapCoordinates(node.x, node.y));
          }
        });
        
        if (depot) {
          coords.push(mapCoordinates(depot.x, depot.y));
        }

        if (coords.length < 2) return null;

        return (
          <div key={`route-group-${idx}`}>
            <Polyline 
              positions={coords} 
              pathOptions={{ 
                color: color, 
                weight: 4, 
                opacity: 0.8,
                lineCap: 'round',
                lineJoin: 'round',
                dashArray: trafficScenario !== 'baseline' ? '10, 10' : undefined 
              }} 
            />
          </div>
        );
      })}
      
      {/* Nodes (Depot and Customers) */}
      {Object.values(nodes).map(node => {
        // Render all nodes as supplied by the backend
        
        return (
          <CircleMarker
            key={`node-${node.id}`}
            center={mapCoordinates(node.x, node.y)}
            radius={node.is_depot ? 8 : 5}
            pathOptions={{
              fillColor: node.is_depot ? '#000000' : '#ffffff',
              color: node.is_depot ? '#ffffff' : '#475569',
              weight: 2,
              fillOpacity: 1
            }}
          >
            <Popup>
              <div className="font-sans">
                <div className="font-bold text-slate-800">{node.is_depot ? 'Depot' : `Customer ${node.id}`}</div>
                {!node.is_depot && <div className="text-xs text-slate-500 mt-1">Node ID: {node.id}</div>}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
