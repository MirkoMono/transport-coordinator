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
  run_id?: string | null;
  matrix_cache_hit?: boolean;
};

export const ROUTE_COLORS = [
  "#f2f2f2",
  "#bfbfbf",
  "#808080",
  "#e0e0e0",
  "#5a5a5a",
];

export const DEMO_CSV = `name,address
Anna Berg,Drottninggatan 1 Stockholm
Björn Lind,Sveavägen 44 Stockholm
Cara Nils,Hornstulls strand 9 Stockholm
David Ek,Storgatan 1 Stockholm
Eva Holm,Årstavägen 12 Stockholm
Felix Ru,Karlbergsvägen 86 Stockholm
Greta Mo,Fleminggatan 18 Stockholm
Hugo Tan,Augustendalsvägen 10 Nacka
Ines Ku,Hägerstensvägen 100 Stockholm
Johan Wi,Råsundavägen 100 Solna
Karin Lo,Götgatan 15 Stockholm
Lars Pe,Fridhemsplan Stockholm`;

export const DEMO_CALL_SHEET = `CALL SHEET - Day 14
Camera - Anna Berg - pickup Drottninggatan 1 Stockholm
Grip - Björn Lind - Sveavägen 44 Stockholm
Sound - Cara Nils - Hornstulls strand 9
AD - David Ek - Storgatan 1 Stockholm
Script - Eva Holm - Årstavägen 12 Stockholm
Electric - Felix Ru - Karlbergsvägen 86 Stockholm
HMU - Hugo Tan - Augustendalsvägen 10 Nacka`;
