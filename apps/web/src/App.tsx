import { useEffect, useState } from "react";
import "./App.css";

type Health = {
  status: string;
  version: string;
  ai_enabled: boolean;
};

type Tab = "map" | "routes" | "fleet" | "account";

const NAV: { id: Tab; label: string }[] = [
  { id: "map", label: "Map" },
  { id: "routes", label: "Routes" },
  { id: "fleet", label: "Fleet" },
  { id: "account", label: "Account" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("map");
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/health")
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`);
        return r.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="greeting">
            Good morning <span className="accent">Coordinator</span>
          </p>
          <p className="subtitle">Film production transport</p>
        </div>
        <button className="icon-btn" aria-label="Settings">
          ⚙
        </button>
      </header>

      <main className="main">
        <section className="card hero">
          <div className="hero-text">
            <p className="label">Today's shoot</p>
            <h1>Transport Coordinator</h1>
            <p className="meta">
              API{" "}
              <span className="accent">
                {health ? health.status : error ? "offline" : "…"}
              </span>
              {health ? ` · v${health.version}` : ""}
            </p>
          </div>
          <div className="hero-badge">Phase 0</div>
        </section>

        <div className="grid-2">
          <section className="card stat">
            <p className="label">Pickups</p>
            <p className="stat-value accent">12</p>
            <p className="meta">demo scenario</p>
          </section>
          <section className="card stat">
            <p className="label">Vehicles</p>
            <p className="stat-value accent">3</p>
            <p className="meta">4-seat vans</p>
          </section>
        </div>

        <section className="card map-placeholder">
          <p className="label">{tab === "map" ? "Route map" : tab}</p>
          <p className="placeholder-text">
            Mapbox integration arrives in Phase 1. Dark-first UI shell is ready.
          </p>
        </section>
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
