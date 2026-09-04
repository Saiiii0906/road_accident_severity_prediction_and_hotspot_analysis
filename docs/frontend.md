# Vantage Frontend Architecture

This document describes the design, folder organization, routing hierarchy, UI components, state management, and export systems of the **Vantage** frontend application.

---

## 1. Technology Stack

- **Framework:** [TanStack Start](https://tanstack.com/start) (Full-stack React framework built on Vite and Nitro).
- **Core Library:** React 19 (`react@^19.2.0`, `react-dom@^19.2.0`).
- **Routing:** `@tanstack/react-router` (Type-safe, file-based routing).
- **Styling:** Tailwind CSS v4 (`tailwindcss@^4.2.1`) with custom theme tokens and utility classes.
- **Component Primitives:** Radix UI (`@radix-ui/react-*`) headless primitives for accessible dialogs, popovers, accordions, and dropdowns.
- **Data Fetching:** `@tanstack/react-query` (`^5.101.1`) for asynchronous API mutations and server caching.
- **Iconography:** Lucide React (`lucide-react@^0.575.0`).
- **Interactive Maps:** Leaflet with custom dark/light tiles.
- **Document Generation:** `jspdf` (`^4.2.1`) with `jspdf-autotable` for client-side vector PDF generation.

---

## 2. Directory Structure

The frontend codebase is located under `frontend/src/`:

```text
frontend/src/
├── components/
│   ├── common/             # Page headers, empty states, metric tiles
│   ├── dashboard/          # Legacy prototype widgets (unreferenced)
│   ├── history/            # History record cards, filter panels, detail views
│   ├── hotspot/            # Hotspot cluster filters, Leaflet map, cluster tables
│   ├── journey/            # Journey input form, telemetry cards, factors, map
│   ├── landing/            # Landing page sections, hero, feature cards, footer
│   ├── layout/             # AppShell, AppSidebar, AppNavbar, theme switcher
│   ├── report/             # AI infrastructure report config, action matrices
│   ├── risk/               # GNN segment tables, risk search filters, road maps
│   ├── severity/           # 16-field collision prediction form, probability charts
│   └── ui/                 # Reusable Radix/Tailwind primitives (buttons, dialogs, inputs)
├── constants/
│   ├── content.ts          # Static copy and domain definitions
│   └── navigation.ts       # Main navigation items and routes
├── hooks/
│   ├── use-mobile.tsx      # Responsive viewport hook (<768px breakpoint)
│   └── use-theme.tsx       # Dark/light theme persistence and toggle
├── lib/
│   ├── api/                # API client abstraction and domain service calls
│   │   ├── client.ts       # Base HTTP client with base URL resolution
│   │   ├── history.ts      # LocalStorage history CRUD operations
│   │   ├── journey.ts      # Journey analysis API mutation
│   │   ├── models.ts       # Severity, Hotspot, and Risk API mutations
│   │   └── reports.ts      # Infrastructure report API mutation
│   ├── pdf/
│   │   ├── journey-pdf-generator.ts # Deterministic 2-page Journey Safety PDF
│   │   └── report-pdf-generator.ts  # Infrastructure Report PDF generator
│   └── utils.ts            # ClassName merge utilities (clsx + tailwind-merge)
├── routes/                 # File-based routes compiled by TanStack Router
│   ├── __root.tsx          # Root layout with HTML document, meta, and theme provider
│   ├── index.tsx           # Public marketing landing page (/)
│   ├── dashboard.tsx       # Journey Safety Analysis workspace (/dashboard)
│   ├── severity-prediction.tsx  # Collision severity prediction form (/severity-prediction)
│   ├── hotspot-explorer.tsx     # Spatial accident cluster map (/hotspot-explorer)
│   ├── road-risk-analysis.tsx   # GNN structural network explorer (/road-risk-analysis)
│   ├── ai-infrastructure-report.tsx # Transport planning report (/ai-infrastructure-report)
│   └── history.tsx         # Local query record history (/history)
├── router.tsx              # Router instantiation
├── routeTree.gen.ts        # Auto-generated route tree
├── server.ts               # Nitro server entrypoint
└── styles.css              # Global styles, Tailwind v4 imports, CSS variables
```

---

## 3. Routing & Page Architecture

TanStack Router automatically compiles routes declared in `frontend/src/routes/`:

| Route Path | Component Mounted | Purpose |
| --- | --- | --- |
| `/` | `IndexPage` (`index.tsx`) | Public landing page with product features, tech stack, and workflow preview. |
| `/dashboard` | `DashboardPage` (`dashboard.tsx`) | Primary operational workspace mounting `JourneySafetyView`. |
| `/severity-prediction` | `SeverityPredictionPage` | Interactive 16-field collision form querying the Random Forest classifier. |
| `/hotspot-explorer` | `HotspotExplorerPage` | Spatial clustering explorer with interactive map and radius/bounding box filters. |
| `/road-risk-analysis` | `RoadRiskPage` | GNN topological risk explorer for UK road segments. |
| `/ai-infrastructure-report` | `AIInfrastructureReportPage` | Multi-model grounded decision-support report generator. |
| `/history` | `HistoryPage` (`history.tsx`) | Inspection of past runs and saved queries across all modules. |

> [!NOTE]
> In the current navigation structure, the `/dashboard` route is labeled "Dashboard" in the sidebar, but its content is dedicated to **Journey Safety Analysis**.

---

## 4. Layout Architecture (`AppShell`)

Authenticated and operational routes share a common layout via `AppShell` (`src/components/layout/app-shell.tsx`):

- **Sidebar (`AppSidebar`):** Collapsible navigation menu displaying product logo, module links, active route highlight, and quick documentation references. Supports mobile drawer behavior via `use-mobile.tsx`.
- **Top Navigation Bar (`AppNavbar`):** Breadcrumb path, theme toggle (dark/light), and quick action controls.
- **Responsive Container:** Flexible content viewport with scrolling containment and responsive grid breakpoints (`sm`, `md`, `lg`, `xl`).

---

## 5. State Management & API Communication

### Asynchronous Data Flow

API interactions avoid complex global state stores (such as Redux) in favor of **React Query** and custom React state:

- The base client (`src/lib/api/client.ts`) resolves `VITE_API_URL` (defaulting to `http://localhost:8000`), formats JSON payloads, sets request headers, and intercepts HTTP error codes.
- Domain modules manage their own request lifecycles using `useState` and `useCallback`, providing explicit `idle`, `loading`, `success`, and `error` states.

### Client-Side History Persistence

The History module (`src/lib/api/history.ts`) does not store records on a remote server. Instead, it maintains a structured list of runs in the browser's `localStorage` under the key:

```typescript
export const HISTORY_STORAGE_KEY = "vantage_analysis_history";
```

Every completed Journey Safety analysis, Severity Prediction, or Infrastructure Report is serialized as a `HistoryRecord` containing:

- Unique ID (`hist-<timestamp>-<random>`)
- Analysis type
- Title, region, and period
- ISO timestamp
- Outcome summary and signals

---

## 6. Client-Side Document Export (PDF Generation)

Vantage provides client-side document export using `jspdf` and `jspdf-autotable`:

### Journey Safety Analysis PDF (`journey-pdf-generator.ts`)

- Generates a clean, 2-page deterministic document without server-side browser dependencies.
- **Page 1:** Executive Summary, AI takeaways, route corridor specifications, live weather/traffic telemetry, and top verified key factors.
- **Page 2:** Itemized supporting evidence inventory, corridor DBSCAN hotspot intersections, GNN road segment risk ratings, actionable recommendations, and explicit data limitations.
- Enforces strict typography sanitization (replacing non-ASCII characters such as em-dashes and directional quotes with ASCII equivalents) to prevent font encoding glitches.

### AI Infrastructure Report PDF (`report-pdf-generator.ts`)

- Compiles a transport planning decision-support briefing from multi-model outputs.
- Formats regional risk signals, prioritized engineering interventions, and an implementation matrix (high/moderate/low impact vs effort).

---

## 7. Notification System Implementation Status

> [!IMPORTANT]
> **Current Notification Status: UI Placeholder (Not Functional)**
> In `frontend/src/components/layout/app-navbar.tsx` (lines 14–23), there is a bell icon button with a static accent dot:
>
> ```tsx
> <Button variant="ghost" size="icon" className="relative text-text-muted hover:text-text-primary">
>   <Bell className="w-5 h-5" />
>   <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent rounded-full" />
> </Button>
> ```
>
> This component is currently a **visual mockup only**:
>
> - There is no `onClick` handler.
> - There is no dropdown popover or notification center.
> - There is no local or remote notification state.
> - There is no WebSocket, Server-Sent Events (SSE), or polling backend connection.
> - Real notification functionality is planned for a later release.

---

## 8. Legacy / Prototype Components

The directory `frontend/src/components/dashboard/` contains five components:

- `kpi-grid.tsx`
- `map-hero.tsx`
- `activity-list.tsx`
- `insights-panel.tsx`
- `analytics-grid.tsx`

These components are **unreferenced prototype artifacts** created during early UI exploration. They are not imported by any active route and rely on hardcoded static numbers in `src/constants/content.ts`. They are scheduled for removal in an upcoming cleanup pass.
