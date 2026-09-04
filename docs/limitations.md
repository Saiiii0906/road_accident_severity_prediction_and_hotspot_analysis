# Vantage System & Scientific Limitations

This document catalogs the scientific, mathematical, geographic, and infrastructural boundaries of the **Vantage** platform. Documenting these constraints ensures that transport analysts, engineers, and evaluators interpret platform outputs with appropriate domain context.

---

## 1. Machine Learning & Statistical Limitations

### 1.1 Severity Prediction Model Scope (Student A)

- **Point-in-Time Crash Classifier:** The Random Forest model evaluates the probable distribution of injury severity (`Fatal`, `Serious`, `Slight`) *assuming that a collision has already occurred* under given road, weather, lighting, and vehicle configurations.
- **Not Prospective Route Risk:** It does **not** estimate the probability or frequency of a collision occurring along a journey. It must not be interpreted as an index of route safety.

### 1.2 Hotspot Density Interpretation (Student B)

- **Density-Based Thresholds:** The DBSCAN algorithm groups accident coordinates that meet a spatial proximity threshold ($\epsilon$) and minimum sample count.
- **Absence Does Not Imply Safety:** If a 1,000-meter corridor buffer contains **0 matched clusters**, this indicates the absence of a historically dense, high-frequency accident cluster. It **does not mean zero collisions have occurred** on that corridor. Scattered or isolated collisions that did not meet cluster density criteria remain outside the hotspot catalog.

### 1.3 Structural Road Risk Interpretation (Student C)

- **Topological Vulnerability vs. Live Danger:** The Graph Neural Network (GNN) scores road segments based on their structural connectivity, junction convergence, and topological position within the road graph.
- **Static Network Representation:** The GNN predictions are computed over structural road graphs. They do not incorporate dynamic real-time fluctuations (e.g. rush-hour volume surges or temporary detours) unless supplemented by live telemetry.

---

## 2. Geographic Coverage & Boundary Limitations

### 2.1 Great Britain National Boundary

- **Training Dataset Origin:** All three machine learning models are trained and calibrated strictly on historical collision records from the **UK Department for Transport (DfT)** covering England, Scotland, and Wales.
- **Coordinate Boundary:**
  $$\text{Latitude: } [50.0^\circ\text{ N}, 60.5^\circ\text{ N}], \quad \text{Longitude: } [-6.5^\circ\text{ E}, 2.0^\circ\text{ E}]$$
- **Non-UK Journeys:** If a user analyzes a route outside Great Britain (e.g. in continental Europe or North America), routing and weather services will operate, but historical models are marked `out_of_bounds`. Extrapolating UK models outside their training geography is strictly prohibited.

### 2.2 Live Telemetry Geographic Scoping (TfL)

- **London-Specific Scope:** Live traffic congestion and active road incident feeds are sourced from the **Transport for London (TfL) Unified API**.
- **Rest of UK:** Outside the Greater London administrative boundary, live traffic delay and incident feeds are marked as `unmonitored` / `unavailable`. Vantage refuses to fabricate synthetic traffic data for unmonitored regions.

---

## 3. Upstream Provider & Infrastructure Limitations

### 3.1 Public Geospatial APIs (Nominatim & OSRM)

- **Nominatim Geocoding:** Relies on the public OpenStreetMap Nominatim endpoint. While cached locally (512 entries, 1h TTL), high-frequency uncached queries are subject to upstream rate limits (1 request/second) and lack a commercial Service Level Agreement (SLA).
- **OSRM Routing:** Uses the public demo routing cluster (`router.project-osrm.org`). Long-distance or highly complex routes may experience transient latency or occasional gateway timeouts.

### 3.2 Atmospheric Telemetry (Open-Meteo)

- **Model Resolution:** Weather forecasts are retrieved from numerical atmospheric models at grid-cell resolutions (typically $1\text{ km} \dots 11\text{ km}$). They represent regional atmospheric forecasts rather than hyper-local microclimates measured by physical roadside sensors.

---

## 4. Architectural & Generative AI Limitations

### 4.1 Absence of a Single Composite Score

- **Intentional Non-Assignment:** `SafetyAssessmentSchema.overall_score` is deliberately set to `None` (**NOT ASSIGNED**).
- **Rationale:** Collapsing heterogeneous physical units (millimeters of rain, traffic delay seconds, cluster frequencies, and graph weights) into a single scalar percentage requires arbitrary, uncalibrated weighting formulas. Vantage rejects arbitrary composite scores in favor of transparent categorical risk factors.

### 4.2 Large Model Memory Footprint

- **Pickle Size:** `student_A/models/accident_severity_model.pkl` is **7.8 GB**.
- **Memory Requirement:** Deserializing this model requires **10 GB to 12 GB RAM**, precluding out-of-the-box deployment on standard low-memory cloud tiers ($\le 4\text{ GB}$).

### 4.3 Generative AI Dependency & Schema Validation

- **Grounded Dependency:** Gemini synthesis relies strictly on the structured evidence payload supplied by backend services. It cannot discover or report hazards that are not present in the ingested telemetry or model outputs.
- **Transient Failures:** During upstream API rate-limits or schema parsing errors, the system gracefully falls back to the deterministic assessment, ensuring no disruption to verified safety metrics.
