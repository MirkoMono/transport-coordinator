# Transport Coordinator — Project Memory

> **Purpose:** Persistent context for AI-assisted development. Read this file at the start of every session.
>
> **Repository:** `transport-coordinator` (dedicated GitHub repo — not part of a monorepo)
>
> **Last updated:** 2026-06-06 (one-click local start, Swedish demo manual, mobile LAN test)

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
POST /api/v1/addresses/bulk-import
POST /api/v1/addresses/geocode-batch          # Nominatim batch (address → lat/lng)
POST /api/v1/routes/optimize
GET  /api/v1/runs                             # route version history
GET  /api/v1/runs/{a}/diff/{b}                # what changed between runs
POST /api/v1/routes/manifest.pdf
POST /api/v1/routes/calendar.ics
POST /api/v1/ai/parse-call-sheet              # optional, requires Ollama + AI_ENABLED=true
GET  /health                                  # includes ai_status
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
| Manual re-optimize after edits | Per-person staggered call times (UI) |
| PWA driver view (read-only manifest) | White-label branding |
| AI call-sheet parsing (optional, Ollama) | NL route edit commands |

**MVP success criteria:**
- [x] 12-person / 12-address scenario solves in < 2 seconds
- [x] Coordinator can import, optimize, and print manifests in < 10 minutes
- [x] Driver opens PWA manifest on phone without app install
- [ ] Full stack runs via `docker compose up` on a MacBook (16 GB RAM, no GPU) — validated via `make setup-local` (no Docker) on dev Mac

---

## 6. Strategic Roadmap

### Phase 0 — Foundation (Week 1–2) ✅
- [x] Initialize GitHub repo `transport-coordinator`
- [x] Monorepo structure: `apps/web`, `apps/api`, `packages/solver`, `docker/`
- [x] Apache 2.0 LICENSE, CONTRIBUTING.md, `.gitignore`
- [x] Docker Compose dev environment (Postgres, Redis, API stub)
- [x] CI: lint + typecheck on push
- [x] Dark-mode UI shell (design tokens from reference sketches)

### Phase 1 — MVP Core (Week 3–6) ✅
- [x] PostGIS schema + migrations (Alembic)
- [x] Address geocoding service (Nominatim default, Mapbox optional)
- [x] Distance matrix service with Redis cache
- [x] OR-Tools VRP solver (replaces Phase 0 placeholder)
- [x] `POST /routes/optimize` end-to-end (persists runs when DB available)
- [x] `POST /addresses/bulk-import` CSV parser
- [x] Coordinator UI: import → configure vehicles → optimize → map view (Leaflet/OSM)
- [x] PDF manifest generation (`fpdf2` + download in UI)

### Phase 2 — Production Polish (Week 7–10) ✅
- [x] Route versioning + diff view ("what changed?")
- [x] Time windows + call-time constraints
- [x] "What-if" mode: lock assignments, re-optimize remainder
- [x] Driver PWA: manifest, check-in, delay report (`/driver`)
- [x] Export: `.ics` calendar per driver
- [x] On-prem install docs + `scripts/install.sh`

### Phase 3 — AI Layer (Week 11–14) 🚧
- [x] `LLMProvider` abstraction (Ollama, disabled fallback) — `packages/ai/`
- [x] Ollama + Gemma 2 in Docker Compose (`docker/compose.ai.yml`, `make ai`)
- [x] Call-sheet text → structured JSON parser (`POST /api/v1/ai/parse-call-sheet`)
- [x] Address-only CSV import + batch geocode (`POST /api/v1/addresses/geocode-batch`)
- [x] UI: import/geocode workflow, AI call-sheet tab, map fit-bounds (`MapFitBounds.tsx`)
- [x] Coordinates from Nominatim only — LLM never outputs lat/lng
- [ ] NL route edit commands
- [ ] Per-person call/pickup times (solver supports `must_arrive_by_minutes`; AI/UI not wired)
- [x] Memory/VRAM guardrails (Ollama container 4 GB limit)

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

## 7. UI Design Reference

**Full spec:** [docs/design.md](docs/design.md)

Target direction: dark **monochrome**, **Inter** type, Swiss strict grid, step-by-step wizard flows, pill/radio selection patterns.

| Principle | Target |
|-----------|--------|
| **Clarity** | One primary action per screen; progress on import/geocode/optimize |
| **Accent** | White inverted CTA on dark; gray-scale route lines on map |
| **Layout** | 480px mobile shell, bottom tabs (Map · Routes · Fleet · History) |
| **Driver PWA** | Radio-list manifest, 48px touch targets, optional dark for 4 AM |
| **Scope** | Import → route → reason → export only (no live GPS UI) |

**UI** per [docs/design.md](docs/design.md) — dark monochrome, Inter, strict Swiss grid.

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
| 2026-06-06 | Dark monochrome + Inter | Mint accent retired; white CTAs, gray map routes, Swiss strict grid per `docs/design.md` |
| 2026-06-06 | **FLX** as permanent app brand | Bold header mark (`font-weight: 900`); production title stays in form field + PDF |
| 2026-06-06 | Set / destination drives depot | Geocode on blur + before optimize; persisted in `tc:production`; VRP depot + map center |
| 2026-06-06 | `./scripts/start.sh` as default dev entry | Single command starts API + web, opens browser; `.run/` pid logs; `make start` / `make stop` |
| 2026-06-06 | macOS Desktop `.command` shortcuts | `make desktop` → Start/Stop on Desktop for non-terminal users |
| 2026-06-06 | Swedish demo manual | `docs/demo-manual-sv.md` + `docs/dela-appen.md` for sharing with production testers |
| 2026-06-06 | Mobile LAN test via `--mobile` | `TRANSPORT_MOBILE=1` binds Vite to LAN; phone opens `http://<mac-ip>:5173/driver` on same Wi‑Fi |
| 2026-06-05 | Geocode via Nominatim, not LLM | Production assistants provide addresses only; LLM hallucinated coords would break map + VRP |
| 2026-06-05 | Address-only CSV workflow | `name,address` columns → batch geocode → optimize; no manual lat/lng |
| 2026-06-05 | `make setup-local` for no-Docker dev | User Mac without Docker Desktop; API + web via `scripts/start-api.sh` / `start-web.sh` |

---

## 13. Session Log — 2026-06-05

### User testing feedback (local Mac, no Docker)
- App runs locally via `make setup-local` ✅
- CSV import, PDF export, optimize + map ✅
- **Map pins were wrong** — demo CSV had hand-picked lat/lng; fixed by address-only + Nominatim geocoding
- **OR-Tools infeasible** — CSV commas in addresses (`Drottninggatan 1, Stockholm`) split columns; cities dropped → geocoded to Göteborg/Helsingborg; fixed CSV parser + demo data
- **Nacka missing** — `Kvarnholmsgatan 10` not in Nominatim; replaced with `Augustendalsvägen 10 Nacka` → 12/12 geocoded
- **Load demo appeared dead** — demo pre-loaded on page open; fixed empty initial textarea + status message
- AI call sheet tab disabled until `AI_ENABLED=true` + Ollama (header shows `AI off`)
- UI polish deferred; next milestone: **on-prem install** for production company tester

### Shipped today (Phase 2 remainder + Phase 3 core)
| Area | Changes |
|------|---------|
| **packages/ai/** | `OllamaProvider`, `DisabledProvider`, `parse_call_sheet_text()` — extracts `{name, address}` from messy text |
| **API** | `POST /api/v1/addresses/geocode-batch`, `POST /api/v1/ai/parse-call-sheet`, `ai_status` on `/health` |
| **Geospatial** | `geocode_batch()` with 1 req/sec Nominatim rate limit |
| **CSV import** | `_parse_csv_address()` joins extra columns when addresses contain commas |
| **Solver** | `max_route_minutes` 480; locked-assignment capacity validation; clearer infeasibility error |
| **Web UI** | `CoordinatorView`: CSV vs AI tabs, Import & geocode, geocoded counter, `RouteMap` fit-bounds, depot marker |
| **Docker** | `docker/compose.ai.yml` — optional Ollama profile (`make ai`) |
| **Dev scripts** | `scripts/start-api.sh`, `scripts/start-web.sh`, `scripts/dev-no-docker.sh`, `docs/on-prem-install.md` |
| **Tests** | `packages/ai/tests/`, `test_geocode_batch.py`, `test_ai_parse.py`, CSV comma test |

### Coordinator workflow (current)
1. **Routes tab** → Set **Production** title + **Set / destination** (geocodes on blur → VRP depot)
2. Load demo (12) → **Import & geocode** (~12 sec, Nominatim)
3. Set call time (default 08:00, applies to all crew)
4. **Optimize routes** → Map / Results / PDF (production name on manifest)
5. **AI call sheet** (optional): paste text → Parse & geocode → same pipeline
6. **Coordinator | Driver** role switch in header; driver view reads `tc:lastRun` + production settings

### Known limitations
- Single global call time in UI; per-person `must_arrive_by_minutes` exists in API but not AI/CSV/UI
- Failed geocodes skipped from optimize (counter shows e.g. `11/12 geocoded`); no per-name failure list yet
- Routes drawn as straight lines (haversine), not road network
- AI requires Docker + Ollama + `gemma2:2b` pull; default `AI_ENABLED=false`

---

## 14. Session Quick-Start

When resuming development:
1. Read this `memory.md`
2. Check `git log --oneline -10` for recent work
3. **Without Docker (default):** `make setup-local` (once) → `./scripts/start.sh` or `make desktop` + double-click Start
4. **Mobile test:** `./scripts/start.sh --mobile` → open printed URL on phone (same Wi‑Fi)
5. **With Docker:** `make setup` → `./scripts/start-api.sh` + `./scripts/start-web.sh` (two terminals)
6. **Share demo:** send repo link + `docs/demo-manual-sv.md`
7. Priority: **on-prem install** → per-person call times → AI reasoning panel → Phase 4 OSS release

### Next application steps (2026-06-06)

| Priority | Work | Why |
|----------|------|-----|
| 1 | **On-prem package** for production tester | `scripts/install.sh`, Docker compose, `.env` docs |
| 2 | **Set marker on map** + set address on PDF manifest | Visual confirmation of shoot location |
| 3 | **Per-person call times** | AI + CSV extract `must_arrive_by_minutes`; wire UI → solver |
| 4 | **Failed geocode list** | Show which crew failed and why before optimize |
| 5 | **AI reasoning** | `explain-route`, infeasibility diagnosis (LAN Ollama) |
| 6 | **NL route edits** | "Move Anna to Van 2" → locked assignment → re-optimize |
| 7 | **Driver offline** | Cache manifest in PWA service worker |
| 8 | **Phase 4 OSS** | GHCR images, demo GIF, issue templates |

---

## 16. Session Log — 2026-06-06

### Shipped today (UI / coordinator experience)

| Area | Changes |
|------|---------|
| **Design system** | `docs/design.md` — dark monochrome, Inter, Swiss strict grid; mint accent retired |
| **Theme tokens** | `index.css` — `#0a0a0a` surfaces, white inverted CTAs, gray route polylines, dark map tiles |
| **Typography** | Inter loaded at 400–900; app icon + PWA manifest updated to monochrome |
| **FLX brand** | Permanent bold **FLX** header (`screen-title-brand`, `font-weight: 900`); production title no longer in header |
| **Production section** | Two-column card: **Production** title input + **Set / destination** address (side-by-side on Routes tab) |
| **Set geocoding** | `geocodeSet()` on blur + before optimize via `POST /api/v1/addresses/geocode`; failed set blocks optimize |
| **Depot / VRP** | Geocoded set coordinates = `depot_latitude/longitude` for solver + map; default Stockholm if empty |
| **Persistence** | `apps/web/src/utils/production.ts` — `tc:production` (title, setAddress, depot); `tc:lastRun` for driver |
| **Role switch** | `RoleSwitch.tsx` — Coordinator \| Driver segmented control in header |
| **Icons** | `Icons.tsx` — white SVG icons (nav, stats, clock); native time picker hidden, white clock overlay |
| **Driver PWA** | Dark theme aligned; shows production title from last run |
| **Map** | Route line colors adjusted for monochrome palette |

### User-validated flow (local Mac)
- `./scripts/start-api.sh` + `./scripts/start-web.sh` → http://localhost:5173
- FLX header, production + set fields, demo import/geocode/optimize working
- Set address geocodes (e.g. Valhallavägen) and drives route depot

### Deferred / follow-ups from today
- Distinct map marker label for set vs crew pickups
- Set address printed on PDF driver manifest
- Geocode status styling (success vs error) for set field

---

## 17. Session Log — 2026-06-06 (local start & sharing)

### Shipped today (developer / distribution experience)

| Area | Changes |
|------|---------|
| **One-command start** | `scripts/start.sh` — background API + web, health wait, opens browser; PIDs/logs in `.run/` |
| **Stop** | `scripts/stop.sh` — graceful shutdown + port fallback |
| **Makefile** | `make start`, `make stop`, `make desktop` |
| **macOS shortcuts** | `Start Transport Coordinator.command` + `Stop…` on Desktop via `install-desktop-shortcut.sh` |
| **Mobile LAN** | `./scripts/start.sh --mobile` — Vite `host` when `TRANSPORT_MOBILE=1`; prints `http://<lan-ip>:5173` |
| **Docs (SV)** | `docs/demo-manual-sv.md` — full demo walkthrough in Swedish |
| **Docs (SV)** | `docs/dela-appen.md` — how to share repo + shortcuts with colleagues |
| **README** | Quick start rewritten around `make setup-local` + `./scripts/start.sh` |
| **Setup hint** | `dev-no-docker.sh` now points to `start.sh` first, two-terminal flow as advanced |

### Distribution workflow (current)
1. Share https://github.com/MirkoMono/transport-coordinator + `docs/demo-manual-sv.md`
2. Recipient: `make setup-local` → `./scripts/start.sh` (or `make desktop`)
3. Demo: Production + Set → Load demo (12) → Import & geocode → Optimize → Map / Driver
4. Team mobile preview: host runs `--mobile`, others open LAN URL on same Wi‑Fi

### User-validated
- Desktop shortcuts installed on dev Mac (`~/Desktop/Start Transport Coordinator.command`)
- `start.sh` brings API + web up without two terminals

---

## 15. Open Questions

- [ ] Primary market: Sweden/Nordics first? (46elks SMS, Swedish call-sheet formats)
- [ ] Map provider default: Mapbox (better UX) vs OSM-only (fully OSS)?
- [ ] Separate `driver-pwa` app or shared React router routes?
- [ ] Enterprise features repo: private `transport-coordinator-enterprise` or monorepo with conditional build?
