# Transport Coordinator — Project Memory

> **Purpose:** Persistent context for AI-assisted development. Read this file at the start of every session.
>
> **Repository:** `transport-coordinator` (dedicated GitHub repo — not part of a monorepo)
>
> **Last updated:** 2026-06-05 (Phase 0 complete)

---

## 1. Product Vision

A **film production transport coordinator** that solves the **Vehicle Routing Problem (VRP)** with pickup constraints: N people at N addresses, assigned to M vehicles with capacity limits, minimizing total transit time and passenger wait.

**Primary users:**
- **Production coordinators** — plan routes, export manifests, handle last-minute changes
- **Drivers** — simple mobile manifests, navigation deep-links, delay reporting
- **Production office** — fleet overview, call-time alignment

**Core value proposition:** Save one coordinator morning per shoot (~$300–500/day). Price at 20–30% of demonstrated savings.

**Example scenario (validated use case):**
> 12 people, 12 different pickup addresses, X vehicles with varying capacity → compute the most efficient vehicle assignment and stop order.

---

## 2. Business Model (Open-Core)

The application is designed for **later open-source release** using an **open-core** model:

| Tier | License | Includes |
|------|---------|----------|
| **Community (OSS)** | Apache 2.0 | VRP solver, CSV import, map UI, PDF manifests, single-tenant Docker deploy, local LLM hooks |
| **Professional** | Commercial subscription | Multi-tenant SaaS, call-sheet sync, real-time traffic rerouting, SMS/email notifications |
| **Enterprise** | Custom license | On-premise air-gapped, SSO/SAML, audit logs, white-label, SLA, custom integrations |

**Why open-core works here:**
- Coordinators and studios increasingly demand **self-hosting** (PII: talent home addresses).
- Open source builds trust and community contributions (new constraint types, locale support).
- Revenue comes from **hosting, integrations, and enterprise compliance** — not the solver itself.

**Pricing reference (from market research):**
- SaaS: $149/mo base, $299/mo with call-sheet sync + live traffic
- Per-project: $200–800/production
- Custom on-prem build: $3,000–8,000 + 20% annual maintenance
- Enterprise studio license: $1,500–4,000/mo

---

## 3. Architecture Principles

### 3.1 Deterministic core, optional AI

```
┌─────────────────────────────────────────────────────────────┐
│  CRITICAL PATH (no GPU, no LLM, always works offline)       │
│  CSV → Geocode → Distance Matrix → OR-Tools VRP → Manifest  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (optional enhancement layer)
┌─────────────────────────────────────────────────────────────┐
│  AI ASSISTANT (pluggable, degrades gracefully if unavailable)│
│  Messy call-sheet parsing · NL schedule edits · delay advice  │
└─────────────────────────────────────────────────────────────┘
```

**The VRP solver must never depend on an LLM.** Optimization is OR-Tools (milliseconds for 12 nodes). AI is additive UX only.

### 3.2 Low-VRAM / local LLM compatibility (Gemma and similar)

Target: stable operation on **consumer hardware and low-VRAM GPUs** (4–8 GB VRAM, or CPU-only).

| Requirement | Implementation |
|-------------|----------------|
| Small models | Default: **Gemma 2 2B/9B** or **Llama 3.2 3B** via Ollama |
| Quantization | Q4_K_M / Q5 — fits 2B models in ~2 GB RAM |
| CPU fallback | llama.cpp backend; AI features disabled if load > threshold |
| No AI required | App is 100% functional with `AI_ENABLED=false` |
| Provider abstraction | `LLMProvider` interface: `ollama`, `openai-compatible`, `disabled` |
| Memory budget | Cap context at 4K tokens; stream responses; no embedding index in MVP |
| Stable under load | AI runs in separate process/container with memory limits (cgroups) |

**AI use cases (post-MVP, optional):**
1. Parse unstructured call-sheet text into structured pickups
2. Natural-language "what-if" edits ("move Anna to car 2")
3. Generate driver SMS summaries
4. Explain why the optimizer chose a particular split

### 3.3 Deployment targets

| Target | Stack |
|--------|-------|
| **Client on-premise** | Docker Compose: `api`, `solver`, `postgres+postgis`, `redis`, `frontend`, optional `ollama`, optional `osrm` |
| **Mobile (drivers)** | PWA — no app store; offline manifest cache; deep-link to Apple/Google Maps |
| **SaaS (later)** | Same containers on K8s/Cloud Run; tenant isolation via schema or row-level security |
| **Air-gapped studio** | Self-hosted Nominatim + OSRM; no external API calls; license key for enterprise features |

### 3.4 Tech stack (locked for MVP)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | React + Vite + TypeScript + Mapbox GL JS | Fast dev, print-quality maps |
| Backend | FastAPI (Python 3.12+) | Native OR-Tools integration |
| Solver | Google OR-Tools Routing Library | Industry standard, Apache 2.0, free |
| Database | PostgreSQL 16 + PostGIS | Geospatial native |
| Cache / queue | Redis + Celery (or ARQ) | Matrix cache, async PDF gen |
| Auth (MVP) | Supabase Auth or simple JWT | Upgrade to SSO in enterprise tier |
| Mobile | React PWA (shared components) | Zero friction for drivers |
| AI (optional) | Ollama + Gemma 2 | Local, private, low VRAM |
| CI/CD | GitHub Actions | Lint, test, Docker build |
| License | Apache 2.0 (core) | Open-source friendly |

---

## 4. System Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Web Frontend │────▶│  API Gateway │────▶│  FastAPI Backend │
│ (Coordinator)│     │  Auth + RL   │     │                  │
└──────────────┘     └──────────────┘     └────────┬─────────┘
┌──────────────┐                                  │
│ Driver PWA   │◄─────────────────────────────────┤
└──────────────┘                                  │
                                                  ▼
                    ┌─────────────┬────────────────┬─────────────┐
                    │ VRP Solver  │ Geospatial Svc │ AI Service  │
                    │ (OR-Tools)  │ (OSRM/Mapbox)  │ (Ollama)    │
                    │ stateless   │ cached matrix  │ optional    │
                    └──────┬──────┴───────┬────────┴──────┬──────┘
                           │              │               │
                           ▼              ▼               ▼
                    ┌──────────────────────────────────────────┐
                    │ PostgreSQL + PostGIS  │  Redis  │  S3/MinIO │
                    └──────────────────────────────────────────┘
```

### Key API endpoints (MVP)

```
POST /api/v1/productions/{id}/addresses/bulk-import
POST /api/v1/productions/{id}/routes/optimize
GET  /api/v1/productions/{id}/routes/{route_id}
GET  /api/v1/productions/{id}/routes/{route_id}/manifest.pdf
GET  /api/v1/drivers/{id}/assignment          # PWA
POST /api/v1/routes/{id}/stops/{stop_id}/check-in
POST /api/v1/ai/parse-call-sheet              # optional, requires LLM
```

### Data model (core entities)

- `productions` — shoot date, base location, default call time
- `people` — name, phone, department, priority, address_id
- `addresses` — raw text, geocoded point (PostGIS), confidence score
- `vehicles` — capacity, type (sedan/van/truck), driver_id, equipment flags
- `routes` — versioned optimization runs (audit: "what changed at 5 AM?")
- `route_stops` — ordered stops with ETA, actual arrival, check-in status
- `distance_matrix_cache` — origin/destination hash → duration seconds

---

## 5. MVP Scope (Phase 1 — Weeks 1–8)

**Goal:** One production company runs a real shoot with the tool.

| In scope | Out of scope (later) |
|----------|----------------------|
| CSV bulk address import | StudioBinder API sync |
| Vehicle capacity config | Real-time traffic rerouting |
| OR-Tools VRP optimization | Native iOS/Android apps |
| Map visualization (color per vehicle) | Multi-tenant SaaS billing |
| PDF driver manifest | SSO / SAML |
| Single-tenant Docker deploy | SMS notifications |
| Manual re-optimize after edits | AI call-sheet parsing |
| PWA driver view (read-only manifest) | White-label branding |

**MVP success criteria:**
- [ ] 12-person / 12-address scenario solves in < 2 seconds
- [ ] Coordinator can import, optimize, and print manifests in < 10 minutes
- [ ] Driver opens PWA manifest on phone without app install
- [ ] Full stack runs via `docker compose up` on a MacBook (16 GB RAM, no GPU)

---

## 6. Strategic Roadmap

### Phase 0 — Foundation (Week 1–2) ✅
- [x] Initialize GitHub repo `transport-coordinator`
- [x] Monorepo structure: `apps/web`, `apps/api`, `packages/solver`, `docker/`
- [x] Apache 2.0 LICENSE, CONTRIBUTING.md, `.gitignore`
- [x] Docker Compose dev environment (Postgres, Redis, API stub)
- [x] CI: lint + typecheck on push
- [x] Dark-mode UI shell (design tokens from reference sketches)

### Phase 1 — MVP Core (Week 3–6)
- [ ] PostGIS schema + migrations (Alembic)
- [ ] Address geocoding service (Nominatim default, Mapbox optional)
- [ ] Distance matrix service with Redis cache
- [ ] OR-Tools VRP solver microservice
- [ ] `POST /routes/optimize` end-to-end
- [ ] Coordinator UI: import → configure vehicles → optimize → map view
- [ ] PDF manifest generation (WeasyPrint or similar)

### Phase 2 — Production Polish (Week 7–10)
- [ ] Route versioning + diff view ("what changed?")
- [ ] Time windows + call-time constraints
- [ ] "What-if" mode: lock assignments, re-optimize remainder
- [ ] Driver PWA: manifest, check-in, delay report
- [ ] Export: `.ics` calendar per driver
- [ ] On-prem install docs + single-command deploy script

### Phase 3 — AI Layer (Week 11–14)
- [ ] `LLMProvider` abstraction (Ollama, OpenAI-compatible, disabled)
- [ ] Ollama + Gemma 2 in Docker Compose (optional profile)
- [ ] Call-sheet text → structured JSON parser
- [ ] NL route edit commands
- [ ] Memory/VRAM guardrails (separate container, 4 GB limit)

### Phase 4 — Open Source Release (Week 15–16)
- [ ] Scrub proprietary placeholders
- [ ] README with quickstart, architecture diagram, demo GIF
- [ ] GitHub Issues templates, Code of Conduct
- [ ] Publish Docker images to GHCR
- [ ] Announce on relevant communities (film production tech, OR-Tools)

### Phase 5 — Commercial Tier (Month 5–6)
- [ ] Multi-tenant auth + billing (Stripe)
- [ ] Call-sheet integrations (CSV templates for StudioBinder, SetHero)
- [ ] Real-time traffic (Google Maps Matrix)
- [ ] SMS/email notifications (Twilio / 46elks)
- [ ] SSO (SAML/OIDC) for enterprise
- [ ] Audit logs + per-production encryption keys

### Phase 6 — Enterprise & Mobile Hardening (Month 7+)
- [ ] Air-gapped installer (offline geocoding + routing)
- [ ] PWA offline-first sync
- [ ] White-label theming
- [ ] Kubernetes Helm chart
- [ ] SLA monitoring, health dashboards

---

## 7. UI Design Reference (from sketches)

Design direction for coordinator + driver interfaces. References only — not pixel-perfect copies.

| Principle | Implementation |
|-----------|----------------|
| **Dark-first** | Pure black (`#000`) background, `#1a1a1a` cards |
| **Accent** | Mint green (`#3dff9a`) for active state, ETAs, highlights |
| **Typography** | Clean sans-serif (Inter/system); text-first lists for driver PWA option |
| **Layout** | Card-based dashboard, 2-column stat grid, large map area |
| **Navigation** | Bottom tab bar: Map · Routes · Fleet · Account |
| **Density** | Minimal chrome — coordinators need fast scanning of pickups/ETAs |
| **Driver PWA** | Distraction-free: large timer/ETA ring, simple stop list, one-tap nav deep-link |

CSS tokens live in `apps/web/src/index.css`. Coordinator and driver can share tokens; driver view gets larger touch targets in Phase 2.

---

## 8. Repository Structure (current)

```
transport-coordinator/
├── apps/
│   ├── api/                 # FastAPI backend
│   ├── web/                 # React coordinator dashboard
│   └── driver-pwa/          # Driver mobile PWA (may share web components)
├── packages/
│   ├── solver/              # OR-Tools VRP logic (pure Python, testable)
│   ├── geospatial/          # Geocoding + matrix clients
│   └── ai/                  # Optional LLM provider abstraction
├── docker/
│   ├── compose.yml          # Full stack
│   ├── compose.dev.yml      # Dev overrides
│   └── compose.ai.yml       # Optional Ollama profile
├── docs/
│   ├── architecture.md
│   ├── on-prem-install.md
│   └── api.md
├── memory.md                # This file
├── LICENSE                    # Apache 2.0
├── CONTRIBUTING.md
└── README.md
```

---

## 9. Open Source Checklist

Before public release, ensure:
- [ ] No API keys or secrets in repo (use `.env.example` only)
- [ ] All dependencies compatible with Apache 2.0 (OR-Tools: Apache 2.0 ✓)
- [ ] Mapbox token required only for enhanced tiles — fallback to OpenStreetMap tiles
- [ ] Enterprise-only code in separate private repo OR feature-flagged modules with clear separation
- [ ] CLA not required for MVP; consider DCO (Developer Certificate of Origin) sign-off

---

## 10. Security & Compliance Notes

- **PII:** Talent home addresses — encrypt at rest (PostgreSQL pgcrypto or application-level), audit access.
- **GDPR:** EU data residency option (Hetzner/Fly.io EU regions); data export + deletion endpoints.
- **On-prem:** No outbound network required in air-gapped mode.
- **AI privacy:** Local Ollama ensures call sheet text never leaves client network.

---

## 11. Development Conventions

- **Language:** Python 3.12+ (backend), TypeScript strict (frontend)
- **Formatting:** Ruff (Python), Prettier + ESLint (TS)
- **Testing:** pytest (solver + API), Vitest (frontend); solver must have golden-file tests for known VRP instances
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`)
- **Branches:** `main` (stable), `develop` (integration), feature branches
- **PRs:** Required for `main`; CI must pass

---

## 12. Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-05 | Open-core with Apache 2.0 | Enables on-prem self-hosting; commercial tier for SaaS/enterprise |
| 2026-06-05 | OR-Tools for VRP (not LLM) | Deterministic, fast, proven; LLM cannot reliably solve VRP |
| 2026-06-05 | Optional Ollama + Gemma 2 for AI | Low VRAM, local/private, degrades gracefully |
| 2026-06-05 | PWA over native apps | Zero install friction for drivers; offline-capable |
| 2026-06-05 | FastAPI + React | Best OR-Tools ergonomics + modern frontend |
| 2026-06-05 | Dedicated GitHub repo | Clean OSS history, independent release cycle |
| 2026-06-05 | Dark-mode UI tokens | Matches reference sketches: black + mint green accent |

---

## 13. Session Quick-Start

When resuming development:
1. Read this `memory.md`
2. Check `git log --oneline -10` for recent work
3. Run `make infra` then `make api` + `make web`
4. MVP priority: **solver correctness → API → coordinator UI → PDF manifest**

---

## 14. Open Questions

- [ ] Primary market: Sweden/Nordics first? (46elks SMS, Swedish call-sheet formats)
- [ ] Map provider default: Mapbox (better UX) vs OSM-only (fully OSS)?
- [ ] Separate `driver-pwa` app or shared React router routes?
- [ ] Enterprise features repo: private `transport-coordinator-enterprise` or monorepo with conditional build?
