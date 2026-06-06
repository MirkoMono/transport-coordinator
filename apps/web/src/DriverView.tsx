import { useEffect, useState } from "react";
import type { OptimizeResult, Pickup, Vehicle } from "./types";
import RoleSwitch from "./components/RoleSwitch";
import { loadProductionSettings } from "./utils/production";
import "./App.css";
import "./DriverView.css";

type StoredRun = {
  result: OptimizeResult;
  pickups: Pickup[];
  depot: { latitude: number; longitude: number };
  productionTitle?: string;
  setAddress?: string;
};

type DriverStop = {
  node_id: string;
  person_name: string;
  sequence: number;
  eta_minutes: number;
  address: string;
  checked_in_at?: string | null;
  delay_minutes?: number | null;
};

export default function DriverView() {
  const [stored, setStored] = useState<StoredRun | null>(null);
  const [vehicleId, setVehicleId] = useState("");
  const [stops, setStops] = useState<DriverStop[]>([]);
  const [driverName, setDriverName] = useState("");
  const [vehicleName, setVehicleName] = useState("");
  const [delayMinutes, setDelayMinutes] = useState(10);
  const [message, setMessage] = useState<string | null>(null);
  const [productionTitle, setProductionTitle] = useState(
    () => loadProductionSettings().title,
  );
  const [setAddress, setSetAddress] = useState(
    () => loadProductionSettings().setAddress,
  );

  useEffect(() => {
    const raw = localStorage.getItem("tc:lastRun");
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as StoredRun;
      setStored(parsed);
      if (parsed.result.routes[0]) {
        setVehicleId(parsed.result.routes[0].vehicle_id);
      }
      if (parsed.productionTitle) {
        setProductionTitle(parsed.productionTitle);
      }
      if (parsed.setAddress) {
        setSetAddress(parsed.setAddress);
      }
    } catch {
      setStored(null);
    }
  }, []);

  useEffect(() => {
    if (!stored || !vehicleId) return;

    const route = stored.result.routes.find((r) => r.vehicle_id === vehicleId);
    if (!route) return;

    setDriverName(route.driver_name);
    setVehicleName(route.vehicle_name);

    const loadStops = async () => {
      if (stored.result.run_id) {
        const res = await fetch(
          `/api/v1/drivers/${vehicleId}/manifest?run_id=${stored.result.run_id}`,
        );
        if (res.ok) {
          const data = (await res.json()) as { stops: DriverStop[] };
          setStops(data.stops);
          return;
        }
      }
      setStops(
        route.stops.map((s) => {
          const person = stored.pickups.find((p) => p.id === s.node_id);
          return {
            node_id: s.node_id,
            person_name: person?.name ?? s.node_id,
            sequence: s.sequence,
            eta_minutes: s.eta_minutes,
            address: person?.address ?? "",
          };
        }),
      );
    };

    loadStops();
  }, [stored, vehicleId]);

  async function checkIn(nodeId: string) {
    if (!stored?.result.run_id) {
      setMessage("Check-in saved locally (no run id)");
      setStops((prev) =>
        prev.map((s) =>
          s.node_id === nodeId ? { ...s, checked_in_at: new Date().toISOString() } : s,
        ),
      );
      return;
    }
    const res = await fetch("/api/v1/drivers/check-in", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: stored.result.run_id,
        vehicle_id: vehicleId,
        node_id: nodeId,
      }),
    });
    if (res.ok) {
      setMessage("Checked in");
      setStops((prev) =>
        prev.map((s) =>
          s.node_id === nodeId ? { ...s, checked_in_at: new Date().toISOString() } : s,
        ),
      );
    } else {
      setMessage("Check-in failed");
    }
  }

  async function reportDelay(nodeId: string) {
    if (!stored?.result.run_id) {
      setMessage("Delay noted locally");
      setStops((prev) =>
        prev.map((s) =>
          s.node_id === nodeId ? { ...s, delay_minutes: delayMinutes } : s,
        ),
      );
      return;
    }
    const res = await fetch("/api/v1/drivers/delay", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: stored.result.run_id,
        vehicle_id: vehicleId,
        node_id: nodeId,
        delay_minutes: delayMinutes,
      }),
    });
    setMessage(res.ok ? `Delay ${delayMinutes} min reported` : "Delay report failed");
  }

  function openMaps(stop: DriverStop) {
    const person = stored?.pickups.find((p) => p.id === stop.node_id);
    if (!person?.latitude || !person?.longitude) return;
    const url = `https://www.google.com/maps/dir/?api=1&destination=${person.latitude},${person.longitude}`;
    window.open(url, "_blank");
  }

  if (!stored) {
    return (
      <div className="driver-app">
        <RoleSwitch />
        <header className="driver-header-block">
          <h1 className="driver-screen-title">
            {productionTitle.trim() || "Manifest"}
          </h1>
          <p className="driver-meta">No route loaded. Optimize in Coordinator first.</p>
          {setAddress && <p className="driver-meta">Set: {setAddress}</p>}
        </header>
      </div>
    );
  }

  const vehicles: Vehicle[] = stored.result.routes.map((r) => ({
    id: r.vehicle_id,
    name: r.vehicle_name,
    capacity: 0,
    driver_name: r.driver_name,
  }));

  const nextStop = stops.find((s) => !s.checked_in_at);

  return (
    <div className="driver-app">
      <RoleSwitch />
      <header className="driver-header-block">
        <h1 className="driver-screen-title">
          {productionTitle.trim() || "Manifest"}
        </h1>
        <p className="driver-meta">
          {driverName || "Driver"}
          {vehicleName ? ` · ${vehicleName}` : ""}
        </p>
        {setAddress && <p className="driver-meta">Set: {setAddress}</p>}
      </header>

      {nextStop && (
        <section className="driver-card focus">
          <p className="label">Next pickup</p>
          <p className="focus-name">{nextStop.person_name}</p>
          <p className="focus-eta accent">ETA {nextStop.eta_minutes} min</p>
          <p className="focus-address">{nextStop.address}</p>
          <div className="btn-row">
            <button className="btn primary" onClick={() => checkIn(nextStop.node_id)}>
              Check in
            </button>
            <button className="btn secondary" onClick={() => openMaps(nextStop)}>
              Navigate
            </button>
          </div>
        </section>
      )}

      <section className="driver-card">
        <label className="label">
          Vehicle
          <select
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            className="driver-select"
          >
            {vehicles.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </label>
        <label className="label delay-label">
          Delay (min)
          <input
            type="number"
            min={0}
            max={120}
            value={delayMinutes}
            onChange={(e) => setDelayMinutes(parseInt(e.target.value, 10))}
            className="delay-input"
          />
        </label>
      </section>

      <section className="driver-card">
        <p className="label">Today's stops</p>
        <ol className="driver-stops">
          {stops.map((stop) => (
            <li key={stop.node_id} className={stop.checked_in_at ? "done" : ""}>
              <div>
                <span className="stop-name">{stop.person_name}</span>
                <span className="stop-eta">ETA {stop.eta_minutes} min</span>
              </div>
              <div className="stop-actions">
                {!stop.checked_in_at && (
                  <>
                    <button className="btn small" onClick={() => checkIn(stop.node_id)}>
                      In
                    </button>
                    <button className="btn small secondary" onClick={() => reportDelay(stop.node_id)}>
                      Late
                    </button>
                    <button className="btn small secondary" onClick={() => openMaps(stop)}>
                      Nav
                    </button>
                  </>
                )}
                {stop.checked_in_at && <span className="badge">Done</span>}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {message && <p className="driver-message">{message}</p>}
    </div>
  );
}
