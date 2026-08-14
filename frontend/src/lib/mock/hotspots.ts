/**
 * DEMO / PRESENTATION DATA ONLY.
 *
 * These values are illustrative placeholders used to exercise the Hotspot
 * Explorer UI before backend integration. They are NOT real-world statistics
 * and the location names are generic corridor labels, not real places.
 *
 * TODO(backend): delete this file once `loadHotspots` reads from the API.
 */

import type { Hotspot, HotspotSummary } from "@/lib/api/hotspots";

export const DEMO_HOTSPOTS: Hotspot[] = [
  {
    id: "hs-01",
    location: "Corridor N4 · Junction 12",
    region: "north",
    intensity: "critical",
    x: 0.28,
    y: 0.24,
    accidentCount: 312,
    severeAccidentCount: 74,
    riskLevel: "Priority intervention",
    dominantConditions: ["Rainfall", "Wet surface", "Dark — lit"],
    recommendedIntervention: "Signalised turn phasing review and anti-skid resurfacing.",
  },
  {
    id: "hs-02",
    location: "Ring Road · Sector 7 approach",
    region: "central",
    intensity: "high",
    x: 0.52,
    y: 0.38,
    accidentCount: 248,
    severeAccidentCount: 51,
    riskLevel: "High",
    dominantConditions: ["Clear weather", "Dry surface", "Heavy traffic"],
    recommendedIntervention: "Speed management and lane-merge redesign at the approach.",
  },
  {
    id: "hs-03",
    location: "Industrial Link Road · Gate 3",
    region: "east",
    intensity: "high",
    x: 0.74,
    y: 0.3,
    accidentCount: 196,
    severeAccidentCount: 43,
    riskLevel: "High",
    dominantConditions: ["Fog or mist", "Surface defects"],
    recommendedIntervention: "Reflective delineation and heavy-vehicle access control.",
  },
  {
    id: "hs-04",
    location: "Old Town Crossing",
    region: "central",
    intensity: "moderate",
    x: 0.44,
    y: 0.62,
    accidentCount: 134,
    severeAccidentCount: 22,
    riskLevel: "Moderate",
    dominantConditions: ["Clear weather", "Dry surface", "Pedestrian activity"],
    recommendedIntervention: "Raised crossing and kerb-line tightening.",
  },
  {
    id: "hs-05",
    location: "Highway Bypass · Km 41",
    region: "south",
    intensity: "critical",
    x: 0.62,
    y: 0.78,
    accidentCount: 287,
    severeAccidentCount: 68,
    riskLevel: "Priority intervention",
    dominantConditions: ["Rainfall", "Wet surface", "High speed"],
    recommendedIntervention: "Barrier upgrade and drainage correction over the curve.",
  },
  {
    id: "hs-06",
    location: "Riverside Avenue",
    region: "west",
    intensity: "moderate",
    x: 0.18,
    y: 0.56,
    accidentCount: 121,
    severeAccidentCount: 18,
    riskLevel: "Moderate",
    dominantConditions: ["Snow or ice", "Roadworks"],
    recommendedIntervention: "Winter treatment priority routing and works-zone signage.",
  },
  {
    id: "hs-07",
    location: "Airport Access Spur",
    region: "east",
    intensity: "low",
    x: 0.83,
    y: 0.6,
    accidentCount: 64,
    severeAccidentCount: 6,
    riskLevel: "Monitor",
    dominantConditions: ["Clear weather", "Dry surface"],
    recommendedIntervention: "Continue routine monitoring; no capital works indicated.",
  },
  {
    id: "hs-08",
    location: "Northern Service Road",
    region: "north",
    intensity: "low",
    x: 0.36,
    y: 0.14,
    accidentCount: 52,
    severeAccidentCount: 4,
    riskLevel: "Monitor",
    dominantConditions: ["Clear weather", "Wet surface"],
    recommendedIntervention: "Routine surface inspection cycle.",
  },
];

export const DEMO_SUMMARY: HotspotSummary = {
  totalHotspots: DEMO_HOTSPOTS.length,
  highRiskHotspots: 4,
  severeConcentration: "31% of severe outcomes",
  mostAffectedArea: "Corridor N4 · Junction 12",
};
