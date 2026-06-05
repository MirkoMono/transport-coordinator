import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import type { LatLngExpression } from "leaflet";
import type { OptimizeResult, Pickup } from "../types";
import { ROUTE_COLORS } from "../types";
import "leaflet/dist/leaflet.css";

// Fix default marker icons in Vite
import iconRetina from "leaflet/dist/images/marker-icon-2x.png";
import icon from "leaflet/dist/images/marker-icon.png";
import shadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconRetinaUrl: iconRetina,
  iconUrl: icon,
  shadowUrl: shadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

type Props = {
  pickups: Pickup[];
  result: OptimizeResult | null;
  depot: { latitude: number; longitude: number };
};

export default function RouteMap({ pickups, result, depot }: Props) {
  const center: LatLngExpression = [depot.latitude, depot.longitude];
  const geocoded = pickups.filter((p) => p.latitude != null && p.longitude != null);

  const pickupById = Object.fromEntries(pickups.map((p) => [p.id, p]));

  return (
    <div className="map-container">
      <MapContainer center={center} zoom={12} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <Marker position={center}>
          <Popup>Depot / Set</Popup>
        </Marker>
        {geocoded.map((p) => (
          <Marker key={p.id} position={[p.latitude!, p.longitude!]}>
            <Popup>{p.name}</Popup>
          </Marker>
        ))}
        {result?.routes.map((route, idx) => {
          const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
          const points: LatLngExpression[] = [
            [depot.latitude, depot.longitude],
            ...route.stops
              .map((s) => pickupById[s.node_id])
              .filter(Boolean)
              .map((p) => [p.latitude!, p.longitude!] as LatLngExpression),
            [depot.latitude, depot.longitude],
          ];
          if (points.length < 2) return null;
          return (
            <Polyline
              key={route.vehicle_id}
              positions={points}
              pathOptions={{ color, weight: 4, opacity: 0.85 }}
            />
          );
        })}
      </MapContainer>
    </div>
  );
}
