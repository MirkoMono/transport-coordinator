export type Pickup = {
  id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  address: string;
};

export type Vehicle = {
  id: string;
  name: string;
  capacity: number;
  driver_name: string;
};

export type RouteStop = {
  node_id: string;
  sequence: number;
  eta_minutes: number;
};

export type VehicleRoute = {
  vehicle_id: string;
  vehicle_name: string;
  driver_name: string;
  stops: RouteStop[];
  total_distance: number;
};

export type OptimizeResult = {
  routes: VehicleRoute[];
  total_distance: number;
  solver_status: string;
};

export const ROUTE_COLORS = [
  "#3dff9a",
  "#3db8ff",
  "#ff9f3d",
  "#ff6b9d",
  "#b87dff",
  "#ffd93d",
];

export const DEMO_CSV = `name,latitude,longitude,address
Anna Berg,59.3293,18.0686,Södermalm Stockholm
Björn Lind,59.3420,18.0500,Vasastan Stockholm
Cara Nils,59.3180,18.0640,Hornstull Stockholm
David Ek,59.3350,18.0900,Östermalm Stockholm
Eva Holm,59.3100,18.0800,Årsta Stockholm
Felix Ru,59.3480,18.0400,Karlberg Stockholm
Greta Mo,59.3250,18.0300,Kungsholmen Stockholm
Hugo Tan,59.3400,18.1100,Gärdet Stockholm
Ines Ku,59.3050,18.0600,Hägersten Stockholm
Johan Wi,59.3550,18.0700,Solna Stockholm
Karin Lo,59.3200,18.1000,Södermalm Sthlm
Lars Pe,59.3300,18.0200,Fridhemsplan Stockholm`;
