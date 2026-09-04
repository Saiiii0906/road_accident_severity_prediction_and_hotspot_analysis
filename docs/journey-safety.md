# Journey Safety Analysis Pipeline

The **Journey Safety Analysis** pipeline is the flagship analytical capability of **Vantage**. It coordinates real-time geocoding, vehicle routing, atmospheric forecasting, live traffic telemetry, spatial corridor hazard alignment, deterministic risk assessment, and grounded generative AI synthesis into a unified, evidence-based safety evaluation.

---

## 1. End-to-End Workflow Stages

```mermaid
flowchart TD
    subgraph Step1 ["1. Input Acquisition"]
        In[User specifies Origin, Destination, Date, Time]
    end

    subgraph Step2 ["2. Spatial Resolution"]
        Geo[Nominatim Forward Geocoding]
        BBoxCheck{Inside UK Bounds?}
        Route[OSRM Driving Route Generation]
    end

    subgraph Step3 ["3. Live Environmental Telemetry"]
        Meteo[Open-Meteo Hourly Weather]
        TfLTraffic[TfL Live Traffic Status]
        TfLIncidents[TfL Road Disruptions Feed]
    end

    subgraph Step4 ["4. Historical Corridor Alignment"]
        Buffer[1,000m Polyline Corridor Buffer]
        MatchHotspots[Match Student B DBSCAN Clusters]
        MatchGNN[Match Student C GNN Segments]
    end

    subgraph Step5 ["5. Deterministic Assessment"]
        ScoreRules[Deterministic Factor Scoring]
        Authority[overall_score = None / Categorical Assessment]
    end

    subgraph Step6 ["6. Generative AI Synthesis"]
        Grounding[Structured JSON Grounding Payload]
        Gemini[Gemini Synthesis (gemini-3.6-flash)]
    end

    subgraph Step7 ["7. Presentation & Export"]
        UI[Interactive Map & Dashboard Cards]
        PDF[Deterministic 2-Page Vector PDF Export]
        History[Local Browser History Persistence]
    end

    In --> Geo --> BBoxCheck
    BBoxCheck -->|Yes| Route
    BBoxCheck -->|No| Route
    Route --> Meteo
    Route --> TfLTraffic
    Route --> TfLIncidents
    Route --> Buffer
    Buffer --> MatchHotspots
    Buffer --> MatchGNN
    Meteo & TfLTraffic & TfLIncidents & MatchHotspots & MatchGNN --> ScoreRules
    ScoreRules --> Authority
    Authority --> Grounding
    Grounding --> Gemini
    Gemini --> UI
    UI --> PDF
    UI --> History
```

---

## 2. Detailed Stage Breakdown

### Stage 1: User Input

The user provides four core parameters:

- `source`: Origin street address, landmark, or postcode (e.g. *"London Victoria Station"*).
- `destination`: Destination address or landmark (e.g. *"Heathrow Airport Terminal 5"*).
- `travel_date`: Date of travel in `YYYY-MM-DD` format.
- `travel_time`: Departure time in `HH:MM` 24-hour format.

### Stage 2: Geocoding & Routing

1. **Geocoding (`GeocodingService`):**
   - Calls the OpenStreetMap Nominatim API with structured query formatting.
   - Enforces an in-memory LRU cache (512 entries, 1-hour TTL) to minimize external network requests.
   - Checks whether coordinates fall within the UK bounding box $[50.0^\circ\text{ N}, 60.5^\circ\text{ N}] \times [-6.5^\circ\text{ E}, 2.0^\circ\text{ E}]$.
2. **Routing (`RoutingService`):**
   - Calls the Project OSRM driving service.
   - Retrieves the optimal vehicle trajectory, turn-by-turn road segment names, overall distance in kilometers, estimated duration in minutes, and an encoded polyline geometry.
   - Decodes the polyline into a sequence of latitude/longitude coordinates.

### Stage 3: Live Telemetry Context

1. **Atmospheric Forecast (`WeatherService`):**
   - Queries Open-Meteo for hourly forecast metrics along the route corridor matching the travel date and time.
   - Extracts temperature ($^\circ\text{C}$), precipitation (mm), visibility (meters), wind speed (km/h), and precipitation probability (%).
   - Flags hazardous driving conditions (e.g. heavy rain $\ge 4\text{ mm/h}$, freezing temperatures $\le 0^\circ\text{C}$, low visibility $\le 1,000\text{ m}$).
2. **Traffic Congestion (`TrafficService`):**
   - Queries the Transport for London (TfL) Unified API for real-time corridor status.
   - Calculates traffic delay multipliers and congestion severities along major corridors (e.g. A4, A40, M4).
   - If the route is outside London, traffic monitoring is marked `unmonitored` / `unavailable`.
3. **Active Road Incidents (`IncidentService`):**
   - Queries the TfL Road Disruption feed for active roadworks, lane closures, emergency utility works, and closures intersecting the route corridor.

### Stage 4: Historical Corridor Alignment (`CorridorMatchingService`)

1. Generates a **1,000-meter buffer corridor** around the route polyline.
2. **DBSCAN Hotspot Matching (`Student B`):**
   - Computes vectorized distances between corridor points and all 3,705 precomputed cluster centroids.
   - Identifies all clusters located within 1,000m of the driving path.
   - Extracts historical collision counts, dominant injury severities, and cluster radii.
3. **GNN Road Segment Matching (`Student C`):**
   - Intersects the route buffer with the 13,921 road segments in the GNN network graph.
   - Identifies segments with elevated structural risk ratings ($p \ge 0.08$) and flags structural bottlenecks.
4. **Severity Prediction Context (`Student A`):**
   - Samples anticipated travel conditions (lighting, surface, weather) at the origin and destination to evaluate the conditional collision severity profile.

### Stage 5: Deterministic Safety Assessment (`SafetyAssessmentService`)

- Evaluates all verified operational, environmental, and historical hazards against deterministic rule sets.
- Aggregates **Key Factors** categorized by severity: `critical`, `high`, `moderate`, `low`, `advisory`, `informational`.
- Compiles an itemized **Supporting Evidence Inventory** with clear factual interpretations.
- Assigns subsystem availability statuses (`available`, `partial`, `unavailable`) for route, weather, traffic, incidents, and historical models.

### Stage 6: Grounded Gemini AI Synthesis (`JourneyPromptService` & `LLMProvider`)

- Translates the structured evidence into an executive takeaway headline, narrative summary, key risk findings, and actionable precautions.
- Strictly enforced by 13 negative grounding constraints (see [AI & Gemini Documentation](ai-gemini.md)).

### Stage 7: User Presentation, PDF Export & History

- **Dashboard:** Interactive Leaflet map displaying route polyline, hotspot markers, live weather widgets, traffic delay chips, and factor lists.
- **PDF Export:** Generates an immediate 2-page deterministic vector PDF document.
- **History Ledger:** Serializes the run into browser `localStorage`.

---

## 3. The "Not Assigned" Overall Score: A Core Design Principle

In Vantage, `SafetyAssessmentSchema.overall_score` is intentionally set to `None` (**NOT ASSIGNED**).

### Why Vantage Refuses to Produce an Arbitrary 0–100 Score

1. **Mathematical Incommensurability:** There is no mathematically valid, objective formula to add millimeters of rainfall to DBSCAN cluster frequencies and GNN graph eigenvalues. Any formula combining them into a single percentage requires arbitrary scalar weights.
2. **Danger of False Reassurance:** A single critical hazard (e.g. black ice on an active bridge closure) creates severe danger. In an averaged 0–100 index, a clear day elsewhere on the journey would mathematically dilute this danger, yielding a misleading "moderate" or "safe" composite score.
3. **Operational Clarity:** Fleet dispatchers and drivers need to know *what* the specific hazards are and *where* they occur, not an opaque aggregate number.

---

## 4. Subsystem Availability & Partial Analysis

Vantage handles degraded external conditions gracefully:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA AVAILABILITY STATUS                        │
├─────────────────┬──────────────────────────────────────────────────────┤
│ AVAILABLE       │ Upstream feed operational; verified real data.       │
│ PARTIAL         │ Segment of route unmonitored (e.g. outside London).  │
│ UNAVAILABLE     │ Upstream API timed out, rate-limited, or failed.     │
│ OUT_OF_BOUNDS   │ Route outside supported geographic coverage (UK).    │
└─────────────────┴──────────────────────────────────────────────────────┘
```

- **Partial Telemetry:** If TfL traffic feeds are unavailable because a journey is between Edinburgh and Glasgow, weather and historical models still execute normally. Traffic is labeled `unmonitored`, and the synthesis explicitly notes this limitation.
- **Zero Matched Hotspots:** If no DBSCAN clusters intersect the 1,000m buffer, the system explicitly reports: *"0 clusters intersected within 1,000m buffer; does not imply zero historical accidents."*
