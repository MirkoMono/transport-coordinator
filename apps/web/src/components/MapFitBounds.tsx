import { useEffect } from "react";
import { useMap } from "react-leaflet";
import type { LatLngExpression } from "leaflet";

type Props = {
  points: LatLngExpression[];
};

export default function MapFitBounds({ points }: Props) {
  const map = useMap();

  useEffect(() => {
    if (points.length < 2) return;
    map.fitBounds(points as [number, number][], { padding: [32, 32], maxZoom: 14 });
  }, [map, points]);

  return null;
}
