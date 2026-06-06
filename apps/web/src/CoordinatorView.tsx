import { useEffect, useState } from "react";
import { IconClock, IconUsers, TAB_ICONS } from "./components/Icons";
import RoleSwitch from "./components/RoleSwitch";
import RouteMap from "./components/RouteMap";
import {
  DEMO_CALL_SHEET,
  DEMO_CSV,
  ROUTE_COLORS,
  type OptimizeResult,
  type Pickup,
  type Vehicle,
} from "./types";
import {
  DEFAULT_DEPOT,
  DEFAULT_SET_ADDRESS,
  loadProductionSettings,
  saveProductionSettings,
  type DepotLocation,
} from "./utils/production";
import { timeStringToMinutes } from "./utils/time";
import "./App.css";

type Health = {
  status: string;
  version: string;
  ai_enabled: boolean;
  ai_status?: string;
  redis?: string;
  database?: string;
};
type Tab = "map" | "routes" | "fleet" | "history";
type RunSummary = {
  id: string;
  created_at: string | null;
  total_distance: number;
};
type DiffResult = {
  assignments: {
    moved: Array<{
      person_name: string;
      from_vehicle: string;
      to_vehicle: string;
    }>;
    added: Array<{ person_name: string; vehicle: string }>;
    removed: Array<{ person_name: string; vehicle: string }>;
  };
  eta_changes: Array<{
    person_name: string;
    old_eta_minutes: number;
    new_eta_minutes: number;
    delta_minutes: number;
  }>;
  distance_delta_meters: number;
};

const NAV: { id: Tab; label: string }[] = [
  { id: "map", label: "Map" },
  { id: "routes", label: "Routes" },
  { id: "fleet", label: "Fleet" },
  { id: "history", label: "History" },
];

const EMPTY_CSV = "name,address\n";

function makeVehicles(count: number, capacity: number): Vehicle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `v${i + 1}`,
    name: `Van ${i + 1}`,
    capacity,
    driver_name: `Driver ${String.fromCharCode(65 + i)}`,
  }));
}

export default function CoordinatorView() {
  const [tab, setTab] = useState<Tab>("routes");
  const [health, setHealth] = useState<Health | null>(null);
  const [csv, setCsv] = useState(EMPTY_CSV);
  const [callSheetText, setCallSheetText] = useState("");
  const [importMode, setImportMode] = useState<"csv" | "ai">("csv");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [pickups, setPickups] = useState<Pickup[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>(makeVehicles(3, 4));
  const [vehicleCount, setVehicleCount] = useState(3);
  const [vehicleCapacity, setVehicleCapacity] = useState(4);
  const [setAddress, setSetAddress] = useState(
    () => loadProductionSettings().setAddress || DEFAULT_SET_ADDRESS,
  );
  const [depot, setDepot] = useState<DepotLocation>(
    () => loadProductionSettings().depot ?? DEFAULT_DEPOT,
  );
  const [setStatus, setSetStatus] = useState<string | null>(null);
  const [callTime, setCallTime] = useState("08:00");
  const [lockedAssignments, setLockedAssignments] = useState<Record<string, string>>({});
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [runHistory, setRunHistory] = useState<RunSummary[]>([]);
  const [diffA, setDiffA] = useState("");
  const [diffB, setDiffB] = useState("");
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [productionTitle, setProductionTitle] = useState(
    () => loadProductionSettings().title,
  );

  useEffect(() => {
    saveProductionSettings({ title: productionTitle, setAddress, depot });
  }, [productionTitle, setAddress, depot]);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json() as Promise<Health>)
      .then(setHealth)
      .catch(() => setHealth(null));
    fetch("/api/v1/runs")
      .then((r) => r.json() as Promise<{ runs: RunSummary[] }>)
      .then((d) => setRunHistory(d.runs))
      .catch(() => setRunHistory([]));
  }, []);

  useEffect(() => {
    setVehicles(makeVehicles(vehicleCount, vehicleCapacity));
  }, [vehicleCount, vehicleCapacity]);

  async function geocodePickups(rows: Pickup[]): Promise<Pickup[]> {
    const needsGeocode = rows.filter((r) => r.latitude == null && r.address);
    if (!needsGeocode.length) return rows;

    setStatusMsg(`Geocoding ${needsGeocode.length} addresses (~1 sec each)...`);
    const res = await fetch("/api/v1/addresses/geocode-batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items: needsGeocode.map((r) => ({
          id: r.id,
          name: r.name,
          address: r.address || r.name,
        })),
        country_bias: "se",
      }),
    });
    if (!res.ok) throw new Error("Geocoding failed");
    const data = (await res.json()) as {
      results: Array<{
        id: string;
        latitude: number | null;
        longitude: number | null;
        address: string;
        display_name: string;
        geocoded: boolean;
      }>;
      failed_count: number;
    };
    const byId = Object.fromEntries(data.results.map((r) => [r.id, r]));
    const merged = rows.map((row) => {
      const hit = byId[row.id];
      if (!hit?.geocoded) return row;
      return {
        ...row,
        latitude: hit.latitude,
        longitude: hit.longitude,
        address: hit.display_name || hit.address || row.address,
      };
    });
    if (data.failed_count > 0) {
      setStatusMsg(`${data.failed_count} address(es) could not be geocoded.`);
    } else {
      setStatusMsg("All addresses geocoded.");
    }
    return merged;
  }

  function loadDemoCsv() {
    setCsv(DEMO_CSV);
    setError(null);
    setStatusMsg("Demo loaded (12 crew). Click Import & geocode next.");
  }

  function loadDemoCallSheet() {
    setCallSheetText(DEMO_CALL_SHEET);
    setError(null);
    setStatusMsg("Demo call sheet loaded. Click Parse & geocode next.");
  }

  async function importCsv() {
    setError(null);
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await fetch("/api/v1/addresses/bulk-import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv, has_header: true }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? res.statusText);
      const data = (await res.json()) as { rows: Pickup[] };
      const geocoded = await geocodePickups(data.rows);
      setPickups(geocoded);
      setResult(null);
      setLockedAssignments({});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  async function parseCallSheet() {
    setError(null);
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await fetch("/api/v1/ai/parse-call-sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: callSheetText }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "AI parse failed");
      }
      const data = (await res.json()) as { rows: Array<{ name: string; address: string }> };
      const rows: Pickup[] = data.rows.map((r) => ({
        id: crypto.randomUUID(),
        name: r.name,
        latitude: null,
        longitude: null,
        address: r.address,
      }));
      const geocoded = await geocodePickups(rows);
      setPickups(geocoded);
      setResult(null);
      setLockedAssignments({});
      setStatusMsg(`AI parsed ${data.rows.length} crew, geocoded for map.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "AI parse failed");
    } finally {
      setLoading(false);
    }
  }

  async function geocodeSet(): Promise<DepotLocation | null> {
    const address = setAddress.trim();
    if (!address) {
      setDepot(DEFAULT_DEPOT);
      setSetStatus(null);
      return DEFAULT_DEPOT;
    }

    setSetStatus("Geocoding set…");
    try {
      const res = await fetch("/api/v1/addresses/geocode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, country_bias: "se" }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Set address not found");
      }
      const data = (await res.json()) as {
        latitude: number;
        longitude: number;
        display_name: string;
      };
      const location = { latitude: data.latitude, longitude: data.longitude };
      setDepot(location);
      setSetAddress(data.display_name || address);
      setSetStatus("Set geocoded.");
      return location;
    } catch (e) {
      setSetStatus(e instanceof Error ? e.message : "Set geocoding failed");
      return null;
    }
  }

  function persistForDriver(data: OptimizeResult) {
    localStorage.setItem(
      "tc:lastRun",
      JSON.stringify({
        result: data,
        pickups,
        depot,
        productionTitle,
        setAddress,
      }),
    );
  }

  async function optimize() {
    setError(null);
    const ready = pickups.filter((p) => p.latitude != null && p.longitude != null);
    if (!ready.length) {
      setError("Import and geocode addresses first.");
      return;
    }

    setLoading(true);
    try {
      let activeDepot = depot;
      if (setAddress.trim()) {
        const geocoded = await geocodeSet();
        if (!geocoded) {
          setError("Could not geocode set / destination. Check the address.");
          return;
        }
        activeDepot = geocoded;
      }

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
          depot_latitude: activeDepot.latitude,
          depot_longitude: activeDepot.longitude,
          call_time_minutes: timeStringToMinutes(callTime),
          locked_assignments: lockedAssignments,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? res.statusText);
      }
      const data = (await res.json()) as OptimizeResult;
      setResult(data);
      persistForDriver(data);
      setTab("map");
      const runsRes = await fetch("/api/v1/runs");
      if (runsRes.ok) {
        const runsData = (await runsRes.json()) as { runs: RunSummary[] };
        setRunHistory(runsData.runs);
        if (runsData.runs.length >= 2) {
          setDiffB(runsData.runs[0].id);
          setDiffA(runsData.runs[1].id);
        } else if (runsData.runs.length === 1) {
          setDiffB(runsData.runs[0].id);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Optimization failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadDiff() {
    if (!diffA || !diffB) return;
    setError(null);
    const res = await fetch(`/api/v1/runs/${diffA}/diff/${diffB}`);
    if (!res.ok) {
      setError("Could not load diff");
      return;
    }
    setDiffResult((await res.json()) as DiffResult);
  }

  async function downloadManifest() {
    if (!result) return;
    const res = await fetch("/api/v1/routes/manifest.pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        production_name: productionTitle.trim() || "Transport Coordinator",
        routes: result.routes.map((route) => ({
          vehicle_name: route.vehicle_name,
          driver_name: route.driver_name,
          total_distance: route.total_distance,
          stops: route.stops.map((s) => {
            const person = pickups.find((p) => p.id === s.node_id);
            return {
              node_id: s.node_id,
              person_name: person?.name ?? s.node_id,
              sequence: s.sequence,
              eta_minutes: s.eta_minutes,
              address: person?.address ?? "",
            };
          }),
        })),
      }),
    });
    if (!res.ok) {
      setError("PDF generation failed");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "driver-manifests.pdf";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function downloadIcs(routeId: string) {
    if (!result) return;
    const route = result.routes.find((r) => r.vehicle_id === routeId);
    if (!route) return;
    const res = await fetch("/api/v1/routes/calendar.ics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        vehicle_name: route.vehicle_name,
        driver_name: route.driver_name,
        depot_departure_minutes: 0,
        stops: route.stops.map((s) => {
          const person = pickups.find((p) => p.id === s.node_id);
          return {
            node_id: s.node_id,
            person_name: person?.name ?? s.node_id,
            sequence: s.sequence,
            eta_minutes: s.eta_minutes,
            address: person?.address ?? "",
          };
        }),
      }),
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${route.vehicle_name.replace(" ", "-").toLowerCase()}.ics`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function setLock(nodeId: string, vehicleId: string) {
    setLockedAssignments((prev) => {
      const next = { ...prev };
      if (!vehicleId) delete next[nodeId];
      else next[nodeId] = vehicleId;
      return next;
    });
  }

  return (
    <div className="app">
      <header className="header">
        <RoleSwitch />
        <div className="header-main">
          <h1 className="screen-title screen-title-brand">FLX</h1>
          {productionTitle.trim() && tab !== "routes" && (
            <p className="subtitle">{productionTitle.trim()}</p>
          )}
          <p className="subtitle">
            API {health?.status ?? "offline"}
            {health?.database === "ok" ? " · DB ok" : ""}
            {health?.ai_enabled ? ` · AI ${health.ai_status ?? "on"}` : " · AI off"}
          </p>
        </div>
      </header>

      <main className="main">
        {tab === "routes" && (
          <>
            <section className="card">
              <div className="grid-2 production-grid">
                <div>
                  <p className="label">Production</p>
                  <input
                    type="text"
                    className="production-input"
                    placeholder="Title, e.g. Day 14"
                    value={productionTitle}
                    onChange={(e) => setProductionTitle(e.target.value)}
                  />
                </div>
                <div>
                  <p className="label">Set / destination</p>
                  <input
                    type="text"
                    className="production-input"
                    placeholder="Address, e.g. Filmstaden"
                    value={setAddress}
                    onChange={(e) => {
                      setSetAddress(e.target.value);
                      setSetStatus(null);
                    }}
                    onBlur={() => {
                      void geocodeSet();
                    }}
                  />
                </div>
              </div>
              {setStatus && <p className="hint">{setStatus}</p>}
            </section>

            <section className="card">
              <p className="label">Import method</p>
              <div className="pill-group" role="group" aria-label="Import method">
                <button
                  type="button"
                  className={`pill ${importMode === "csv" ? "selected" : ""}`}
                  onClick={() => setImportMode("csv")}
                >
                  CSV (addresses)
                </button>
                <button
                  type="button"
                  className={`pill ${importMode === "ai" ? "selected" : ""}`}
                  onClick={() => setImportMode("ai")}
                  disabled={!health?.ai_enabled}
                  title={health?.ai_enabled ? "Parse call sheet with Gemma" : "Enable AI_ENABLED in API"}
                >
                  AI call sheet
                </button>
              </div>
              {loading && statusMsg?.includes("Geocoding") && (
                <div className="progress-wrap" aria-live="polite">
                  <div className="progress-label">
                    <span>{statusMsg}</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill indeterminate" />
                  </div>
                </div>
              )}
              {importMode === "csv" ? (
                <>
                  <textarea className="csv-input" value={csv} onChange={(e) => setCsv(e.target.value)} rows={5} />
                  <div className="btn-row">
                    <button type="button" className="btn secondary" onClick={loadDemoCsv}>
                      Load demo (12)
                    </button>
                    <button type="button" className="btn primary" onClick={importCsv} disabled={loading}>
                      Import &amp; geocode
                    </button>
                  </div>
                  <p className="hint">Step 1: Load demo · Step 2: Import &amp; geocode (~12 sec)</p>
                </>
              ) : (
                <>
                  <p className="label">Paste messy call sheet — Gemma extracts names + addresses</p>
                  <textarea
                    className="csv-input"
                    value={callSheetText}
                    onChange={(e) => setCallSheetText(e.target.value)}
                    rows={8}
                  />
                  <div className="btn-row">
                    <button type="button" className="btn secondary" onClick={loadDemoCallSheet}>
                      Load demo
                    </button>
                    <button type="button" className="btn primary" onClick={parseCallSheet} disabled={loading}>
                      Parse &amp; geocode
                    </button>
                  </div>
                </>
              )}
              {statusMsg && !loading && <p className="status-msg">{statusMsg}</p>}
            </section>

            <div className="grid-2">
              <section className="card stat">
                <p className="label label-with-icon">
                  <IconUsers size={14} />
                  Pickups
                </p>
                <p className="stat-value accent">{pickups.length || "—"}</p>
                {pickups.length > 0 && (
                  <p className="hint">
                    {pickups.filter((p) => p.latitude != null).length}/{pickups.length} geocoded
                  </p>
                )}
              </section>
              <section className="card stat">
                <p className="label label-with-icon">
                  <IconClock size={14} />
                  Call time
                </p>
                <div className="time-input-wrap">
                  <input
                    type="time"
                    className="call-time-input"
                    value={callTime}
                    onChange={(e) => setCallTime(e.target.value)}
                    aria-label="Call time"
                  />
                  <IconClock size={18} className="time-input-icon" />
                </div>
              </section>
            </div>

            <section className="card">
              <button className="btn primary full" onClick={optimize} disabled={loading || !pickups.length}>
                {loading ? "Optimizing…" : Object.keys(lockedAssignments).length ? "Re-optimize (locked)" : "Optimize routes"}
              </button>
              {Object.keys(lockedAssignments).length > 0 && (
                <p className="hint">{Object.keys(lockedAssignments).length} locked assignment(s)</p>
              )}
            </section>

            {result && (
              <section className="card">
                <div className="results-header">
                  <p className="label">Results</p>
                  <div className="btn-row">
                    <button className="btn secondary" onClick={downloadManifest}>
                      PDF
                    </button>
                  </div>
                </div>
                <p className="meta accent">
                  {(result.total_distance / 1000).toFixed(1)} km
                  {result.run_id ? ` · run ${result.run_id.slice(0, 8)}` : ""}
                </p>
                {result.routes.map((route, idx) => (
                  <div key={route.vehicle_id} className="route-card">
                    <div className="route-title-row">
                      <p
                        className="route-title"
                        style={{ color: ROUTE_COLORS[idx % ROUTE_COLORS.length] }}
                      >
                        {route.vehicle_name}
                        {route.driver_name ? ` · ${route.driver_name}` : ""}
                      </p>
                      <button className="btn small secondary" onClick={() => downloadIcs(route.vehicle_id)}>
                        ICS
                      </button>
                    </div>
                    <ol className="stop-list">
                      {route.stops.map((s) => {
                        const person = pickups.find((p) => p.id === s.node_id);
                        return (
                          <li key={s.node_id}>
                            <span>
                              {person?.name ?? s.node_id}
                              <span className="eta"> ETA {s.eta_minutes} min</span>
                            </span>
                            <select
                              className="lock-select"
                              value={lockedAssignments[s.node_id] ?? ""}
                              onChange={(e) => setLock(s.node_id, e.target.value)}
                              aria-label={`Lock ${person?.name} to vehicle`}
                            >
                              <option value="">—</option>
                              {vehicles.map((v) => (
                                <option key={v.id} value={v.id}>
                                  Lock {v.name}
                                </option>
                              ))}
                            </select>
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
            {result ? (
              <RouteMap pickups={pickups} result={result} depot={depot} />
            ) : (
              <p className="placeholder-text">Optimize routes first.</p>
            )}
          </section>
        )}

        {tab === "fleet" && (
          <section className="card">
            <div className="input-row">
              <label>
                Vehicles
                <input type="number" min={1} max={12} value={vehicleCount} onChange={(e) => setVehicleCount(parseInt(e.target.value, 10))} />
              </label>
              <label>
                Capacity
                <input type="number" min={1} max={20} value={vehicleCapacity} onChange={(e) => setVehicleCapacity(parseInt(e.target.value, 10))} />
              </label>
            </div>
            <ul className="fleet-list">
              {vehicles.map((v) => (
                <li key={v.id}>{v.name} — {v.capacity} seats — {v.driver_name}</li>
              ))}
            </ul>
          </section>
        )}

        {tab === "history" && (
          <section className="card">
            <p className="label">What changed?</p>
            <p className="hint">Compare two saved runs (requires database).</p>
            <div className="input-row">
              <label>
                Before
                <select value={diffA} onChange={(e) => setDiffA(e.target.value)} className="driver-select">
                  <option value="">Select run</option>
                  {runHistory.map((r) => (
                    <option key={r.id} value={r.id}>{r.created_at?.slice(0, 16) ?? r.id.slice(0, 8)}</option>
                  ))}
                </select>
              </label>
              <label>
                After
                <select value={diffB} onChange={(e) => setDiffB(e.target.value)} className="driver-select">
                  <option value="">Select run</option>
                  {runHistory.map((r) => (
                    <option key={r.id} value={r.id}>{r.created_at?.slice(0, 16) ?? r.id.slice(0, 8)}</option>
                  ))}
                </select>
              </label>
            </div>
            <button className="btn primary full" onClick={loadDiff} disabled={!diffA || !diffB}>
              Compare runs
            </button>
            {diffResult && (
              <div className="diff-panel">
                <p className="meta">Distance delta: {(diffResult.distance_delta_meters / 1000).toFixed(1)} km</p>
                {diffResult.assignments.moved.map((m) => (
                  <p key={m.person_name} className="diff-line">
                    <span className="accent">{m.person_name}</span> moved {m.from_vehicle} → {m.to_vehicle}
                  </p>
                ))}
                {diffResult.eta_changes.map((c) => (
                  <p key={c.person_name} className="diff-line">
                    {c.person_name}: ETA {c.old_eta_minutes} → {c.new_eta_minutes} min ({c.delta_minutes >= 0 ? "+" : ""}{c.delta_minutes})
                  </p>
                ))}
                {!diffResult.assignments.moved.length && !diffResult.eta_changes.length && (
                  <p className="placeholder-text">No significant changes.</p>
                )}
              </div>
            )}
          </section>
        )}

        {error && <p className="error">{error}</p>}
      </main>

      <nav className="bottom-nav">
        {NAV.map((item) => {
          const Icon = TAB_ICONS[item.id];
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
