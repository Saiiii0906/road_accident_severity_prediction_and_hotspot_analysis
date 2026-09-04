# Vantage Machine Learning Models

This document details the mathematical methodology, feature engineering pipelines, training provenance, and operational boundaries of the three machine learning models powering **Vantage**.

---

## 1. Terminology: Public Product Names vs. Internal Identifiers

To prevent confusing end users and transport evaluators, Vantage enforces clear terminology distinctions:

| Public Product Module | Internal Implementation Identifier | Model Type | Core Artifact Location |
| --- | --- | --- | --- |
| **Severity Prediction** | `Student A` | 138-Feature Random Forest Classifier | `student_A/models/accident_severity_model.pkl` |
| **Hotspot Explorer** | `Student B` | Spatial DBSCAN Clustering | `data/output/hotspot_summary.csv` |
| **Road Risk Analysis** | `Student C` | Graph Neural Network (GNN) | `student_C/gnn_risk_predictions.json` |

---

## 2. Severity Prediction (Internal: Student A)

### Severity Prediction Purpose & Scope

The Severity Prediction model evaluates the prospective injury severity distribution **given that a collision occurs** under a specific set of environmental, operational, and structural conditions.

> [!WARNING]
> **Crash-Level vs. Route-Level Risk**  
> This model is a **point-in-time, conditional crash-severity classifier**. It answers: *"If a vehicle collision occurs under these specific conditions, what is the probability that it results in a Fatal, Serious, or Slight injury?"*  
> It does **not** predict the probability that a crash will happen along a route. Treating this model as a prospective route-wide hazard score is statistically invalid.

### Model Architecture & Specs

- **Algorithm:** Scikit-Learn `RandomForestClassifier` (100 estimators).
- **Target Variable:** Accident Severity with 3 classes:
  1. `Fatal` (Death within 30 days of collision)
  2. `Serious` (Hospitalization, severe injury)
  3. `Slight` (Minor cuts, bruising, whiplash)
- **Input Dimensionality:** 138 binary and continuous features after one-hot transformation.
- **Model Binary Footprint:** **7.8 GB** (uncompressed pickle containing deep decision trees).

### Feature Engineering (`StudentATransformer`)

Incoming requests from the UI or API are transformed in `backend/app/services/student_a_transformer.py`:

- **Temporal Transformation:** `time_of_day` (`HH:MM`) is extracted into integer hours; `day_of_week` is one-hot encoded.
- **Environmental Factors:** `light_conditions`, `weather_conditions`, and `road_surface_conditions` are mapped to categorical dummy columns.
- **Road & Traffic Dynamics:** `road_type`, `speed_limit`, `first_road_class`, and `junction_detail` are standardized.
- **Vehicle-Casualty Interaction:** `num_vehicles` and `num_casualties` provide numerical scaling. Traffic density is mapped dynamically from vehicle volume.

---

## 3. Hotspot Explorer (Internal: Student B)

### Hotspot Explorer Purpose & Scope

The Hotspot Explorer identifies empirical clusters of high collision frequency across Great Britain, allowing users to isolate geographic locations with disproportionate accident concentrations.

### Methodology: DBSCAN Density-Based Clustering

- **Algorithm:** Density-Based Spatial Clustering of Applications with Noise (DBSCAN) applied over historical crash coordinates.
- **Distance Metric:** Haversine great-circle distance on the spherical earth model ($R = 6,371\text{ km}$).
- **Precomputed Clusters:** **3,705 discrete clusters** indexed in `data/output/hotspot_summary.csv`.

### Cluster Attributes

Each detected cluster record contains:

- `cluster_id`: Unique integer identifier.
- `latitude`, `longitude`: Spatial centroid of the cluster.
- `accident_count`: Total historical collisions within the cluster boundary.
- `severity_breakdown`: Itemized count of `Fatal`, `Serious`, and `Slight` accidents.
- `dominant_severity`: The most prevalent severity class in the cluster.
- `radius_meters`: Spatial extent (maximum distance from centroid to member collisions).

> [!IMPORTANT]
> **Zero Hotspots $\ne$ Zero Accidents**  
> DBSCAN requires a minimum density threshold (`min_samples` within distance $\epsilon$) to form a cluster. If a spatial query or route buffer intersects **0 clusters**, it means there are no *high-density recurring crash hotspots* in that area. It does **not** mean that zero collisions have ever occurred there.

---

## 4. Road Risk Analysis (Internal: Student C)

### Road Risk Analysis Purpose & Scope

Road Risk Analysis models the structural and topological vulnerability of the physical road network using graph-based deep learning.

### Methodology: Road Network Graph Neural Network (GNN)

Unlike point-based clustering, the GNN views the highway system as an interconnected graph $G = (V, E)$:

- **Nodes ($V$):** Intersections, junctions, roundabouts, and topological transition points.
- **Edges ($E$):** 13,921 road segments across the primary UK road network.
- **Message Passing:** The GNN aggregates topological features across adjacent road links, incorporating:
  - Node degree and centrality (traffic convergence bottlenecks).
  - Edge betweenness (likelihood of carrying regional through-traffic).
  - Road classification and speed hierarchies.

### Output Risk Ratings & Calibration

The GNN outputs a continuous structural risk probability $p \in [0.0, 1.0]$ for each road segment, mapped into four operational categories:

| Risk Category | Predicted Risk ($p$) | Interpretation |
| --- | --- | --- |
| **Low** | $p < 0.05$ | Low topological vulnerability; standard road geometry and flow. |
| **Moderate** | $0.05 \le p < 0.08$ | Moderate structural complexity; typical junction density. |
| **High** | $0.08 \le p < 0.10$ | High topological convergence; elevated incident vulnerability. |
| **Critical** | $p \ge 0.10$ | Critical structural bottleneck or high-risk multi-junction arterial. |

### Corridors & Query Modes

The backend (`backend/app/services/risk_service.py`) indexes the 13,921 segments in NumPy arrays (`student_C/gnn_risk_predictions.json`), allowing instant sub-millisecond filtering by:

1. **UK Road Number:** Querying all segments comprising a specific road (e.g. A1, M25, A406).
2. **Spatial Bounding Box:** Querying segments bounded by geographic coordinates.
3. **Point & Radius:** Identifying all network links within $r\text{ km}$ of a location.
