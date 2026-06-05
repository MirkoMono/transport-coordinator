import { useEffect, useState } from "react";
import RouteMap from "./components/RouteMap";
import { DEMO_CSV, type OptimizeResult, type Pickup, type Vehicle } from "./types";
import "./App.css";

type Health = { status: string; version: string; ai_enabled: boolean };
type Tab = "map" | "routes" | "fleet" | "account";

const NAV: { id: Tab; label: string }[] = [
  { id: "map", label: "Map" },
  { id: "routes", label: "Routes" },
  { id: "fleet", label: "Fleet" },
  { id: "account", label: "Account" },
];

const DEFAULT_DEPOT = { latitude: 59.3293, longitude: 18.0686 };

function makeVehicles(count: number, capacity: number): Vehicle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `v${i + 1}`,
    name: `Van ${i + 1}`,
    capacity,
    driver_name: `Driver ${String.fromCharCode(65 + i)}`,
  }));
}

export default function App() {
  const [tab, setTab] = useState<Tab>("routes");
  const [health, setHealth] = useState<Health | null>(null);
  const [csv, setCsv] = useState(DEMO_CSV);
  const [pickups, setPickups] = useState<Pickup[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>(makeVehicles(3, 4));
  const [vehicleCount, setVehicleCount] = useState(3);
  const [vehicleCapacity, setVehicleCapacity] = useState(4);
  const [depot, setDepot] = useState(DEFAULT_DEPOT);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json() as Promise<Health>)
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    setVehicles(makeVehicles(vehicleCount, vehicleCapacity));
  }, [vehicleCount, vehicleCapacity]);

  async function importCsv() {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/v1/addresses/bulk-import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv, has_header: true }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? res.statusText);
      const data = (await res.json()) as { rows: Pickup[] };
      setPickups(data.rows);
      setResult(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  async function optimize() {
    setError(null);
    const ready = pickups.filter((p) => p.latitude != null && p.longitude != null);
    if (!ready.length) {
      setError("Import CSV with latitude/longitude first.");
      return;
    }
    if (ready.length < pickups.length) {
      setError(`${pickups.length - ready.length} pickup(s) missing coordinates.`);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/v1/routes/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pickups: ready.map((p) => ({
            id: p.id,
            name: p.name,
            latitude: p.latitude,
            longitude: p.longitude,
            address: p.address,
          })),
          vehicles,
          depot_latitude: depot.latitude,
          depot_longitude: depot.longitude,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? res.statusText);
      }
      const data = (await res.json()) as OptimizeResult;
      setResult(data);
      setTab("map");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Optimization failed");
    } finally {
      setLoading(false);
    }
  }

  const geocodedCount = pickups.filter((p) => p.latitude != null).length;

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="greeting">
            Good morning <span className="accent">Coordinator</span>
          </p>
          <p className="subtitle">
            API {health?.status ?? "offline"}
            {health ? ` · v${health.version}` : ""}
          </p>
        </div>
        <button className="icon-btn" aria-label="Settings">
          ⚙
        </button>
      </header>

      <main className="main">
        {tab === "routes" && (
          <>
            <section className="card">
              <p className="label">Import crew CSV</p>
              <p className="hint">Columns: name, latitude, longitude, address</p>
              <textarea
                className="csv-input"
                value={csv}
                onChange={(e) => setCsv(e.target.value)}
                rows={6}
              />
              <div className="btn-row">
                <button className="btn secondary" onClick={() => setCsv(DEMO_CSV)}>
                  Load demo (12)
                </button>
                <button className="btn primary" onClick={importCsv} disabled={loading}>
                  Import
                </button>
              </div>
            </section>

            <div className="grid-2">
              <section className="card stat">
                <p className="label">Pickups</p>
                <p className="stat-value accent">{pickups.length || "—"}</p>
                <p className="meta">{geocodedCount} geocoded</p>
              </section>
              <section className="card stat">
                <p className="label">Vehicles</p>
                <p className="stat-value accent">{vehicleCount}</p>
                <p className="meta">{vehicleCapacity} seats each</p>
              </section>
            </div>

            <section className="card">
              <p className="label">Depot / set location</p>
              <div className="input-row">
                <label>
                  Lat
                  <input
                    type="number"
                    step="0.0001"
                    value={depot.latitude}
                    onChange={(e) =>
                      setDepot({ ...depot, latitude: parseFloat(e.target.value) })
                    }
                  />
                </label>
                <label>
                  Lng
                  <input
                    type="number"
                    step="0.0001"
                    value={depot.longitude}
                    onChange={(e) =>
                      setDepot({ ...depot, longitude: parseFloat(e.target.value) })
                    }
                  />
                </label>
              </div>
              <button
                className="btn primary full"
                onClick={optimize}
                disabled={loading || pickups.length === 0}
              >
                {loading ? "Optimizing…" : "Optimize routes"}
              </button>
            </section>

            {result && (
              <section className="card">
                <p className="label">Results</p>
                <p className="meta accent">
                  {result.solver_status} · {(result.total_distance / 1000).toFixed(1)} km total
                </p>
                {result.routes.map((route) => (
                  <div key={route.vehicle_id} className="route-card">
                    <p className="route-title">
                      {route.vehicle_name}
                      {route.driver_name ? ` · ${route.driver_name}` : ""}
                    </p>
                    <ol className="stop-list">
                      {route.stops.map((s) => {
                        const person = pickups.find((p) => p.id === s.node_id);
                        return (
                          <li key={s.node_id}>
                            {person?.name ?? s.node_id}
                            <span className="eta">ETA {s.eta_minutes} min</span>
                          </li>
                        );
                      })}
                    </ol>
                  </div>
                ))}
              </section>
            )}
          </>
        )}

        {tab === "map" && (
          <section className="card map-card">
            <p className="label">Route map</p>
            {result ? (
              <RouteMap pickups={pickups} result={result} depot={depot} />
            ) : (
              <p className="placeholder-text">Optimize routes first to see the map.</p>
            )}
          </section>
        )}

        {tab === "fleet" && (
          <section className="card">
            <p className="label">Fleet configuration</p>
            <div className="input-row">
              <label>
                Vehicles
                <input
                  type="number"
                  min={1}
                  max={12}
                  value={vehicleCount}
                  onChange={(e) => setVehicleCount(parseInt(e.target.value, 10))}
                />
              </label>
              <label>
                Capacity each
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={vehicleCapacity}
                  onChange={(e) => setVehicleCapacity(parseInt(e.target.value, 10))}
                />
              </label>
            </div>
            <ul className="fleet-list">
              {vehicles.map((v) => (
                <li key={v.id}>
                  {v.name} — {v.capacity} seats — {v.driver_name}
                </li>
              ))}
            </ul>
          </section>
        )}

        {tab === "account" && (
          <section className="card">
            <p className="label">Account</p>
            <p className="placeholder-text">
              Auth and production settings arrive in Phase 2.
            </p>
          </section>
        )}

        {error && <p className="error">{error}</p>}
      </main>

      <nav className="bottom-nav">
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${tab === item.id ? "active" : ""}`}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
