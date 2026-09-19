import { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// Fix Leaflet's default icon path issues with Webpack/Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons
const depotIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const customerIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

interface MapAreaProps {
  nodes: Record<number, { id: number, x: number, y: number, is_depot: boolean }>;
  routes: number[][];
  trafficEdges?: [number, number][]; // optional congestion edges
  depot?: [number, number] | null;
  customers?: [number, number][];
  onMapClick?: (lat: number, lng: number) => void;
  interactionMode?: 'view' | 'depot' | 'customer';
}

function MapClickHandler({ onClick }: { onClick?: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      if (onClick) onClick(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

const COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function MapArea({ nodes, routes, depot, customers, onMapClick, interactionMode }: MapAreaProps) {
  const center: [number, number] = useMemo(() => {
    // Center on Bengaluru by default if no nodes
    if (Object.keys(nodes).length > 0) {
      const firstNode = Object.values(nodes)[0];
      if (firstNode.y !== 0) return [firstNode.y, firstNode.x];
    }
    return [12.9716, 77.5946];
  }, [nodes]);

  // Decode routes into polylines
  const polylines = useMemo(() => {
    return routes.map((route, idx) => {
      return route.map(nodeId => {
        const n = nodes[nodeId];
        return n ? [n.y, n.x] as [number, number] : null;
      }).filter(p => p !== null) as [number, number][];
    });
  }, [routes, nodes]);

  // If we have explicit depot and customers (from clicks)
  const renderedDepot = depot || (Object.values(nodes).find(n => n.is_depot) ? [Object.values(nodes).find(n => n.is_depot)!.y, Object.values(nodes).find(n => n.is_depot)!.x] : null);
  const renderedCustomers = customers || Object.values(nodes).filter(n => !n.is_depot).map(n => [n.y, n.x] as [number, number]);

  return (
    <div className={`h-full w-full relative ${interactionMode !== 'view' ? 'cursor-crosshair' : ''}`}>
      <MapContainer 
        center={center} 
        zoom={13} 
        style={{ width: '100%', height: '100%', background: '#0a0a0f' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-tiles"
        />
        
        <MapClickHandler onClick={onMapClick} />

        {/* Routes */}
        {polylines.map((path, idx) => (
          <Polyline 
            key={`route-${idx}`}
            positions={path}
            color={COLORS[idx % COLORS.length]}
            weight={3}
            opacity={0.8}
          />
        ))}

        {/* Depot */}
        {renderedDepot && (
          <Marker position={renderedDepot as [number, number]} icon={depotIcon} />
        )}

        {/* Customers */}
        {renderedCustomers.map((pos, idx) => (
          <Marker key={`customer-${idx}`} position={pos} icon={customerIcon} />
        ))}
      </MapContainer>
    </div>
  );
}
