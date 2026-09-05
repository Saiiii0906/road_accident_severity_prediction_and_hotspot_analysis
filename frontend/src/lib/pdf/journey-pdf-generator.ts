/**
 * Journey Safety Analysis PDF Generator.
 *
 * Generates an evidence-grounded, publication-quality PDF document
 * from the already available in-memory JourneyAnalyzeResponse state using jsPDF.
 *
 * STRICT INVARIANTS:
 * - Operates entirely client-side on the provided result object.
 * - Does NOT trigger any backend API, routing, weather, traffic, or Gemini calls.
 * - Preserves deterministic scoring invariants: overall_score remains unassigned.
 * - Does NOT extrapolate historical models outside supported UK geography.
 * - Accurately states Hotspot Explorer cluster absence without claiming zero accidents.
 * - Uses standardized public model names:
 *     Student A -> Severity Prediction
 *     Student B -> Hotspot Explorer (DBSCAN)
 *     Student C -> Road Risk Analysis (GNN)
 */

import { jsPDF } from "jspdf";
import type { DataAvailabilityStatus, JourneyAnalyzeResponse } from "@/lib/api/journey";

const SEVERITY_COLORS: Record<string, [number, number, number]> = {
  critical: [220, 38, 38], // #dc2626 red
  high: [234, 88, 12], // #ea580c orange
  moderate: [217, 119, 6], // #d97706 amber
  low: [37, 99, 235], // #2563eb blue
  advisory: [79, 70, 229], // #4f46e5 indigo
  informational: [71, 85, 105], // #475569 slate-600
  unknown: [100, 116, 139], // #64748b slate
};

const STATUS_COLORS: Record<DataAvailabilityStatus, [number, number, number]> = {
  available: [22, 163, 74], // #16a34a green
  partial: [2, 132, 199], // #0284c7 light-blue
  unavailable: [220, 38, 38], // #dc2626 red
  pending: [100, 116, 139], // #64748b slate
};

/**
 * Sanitizes internal model nomenclature into public-facing terminology.
 * Compound phrases are replaced first to prevent duplicated tokens.
 */
export function sanitizePublicModelNames(text: string): string {
  if (!text) return "";
  return text
    .replace(/\bStudent\s*A\s*(?:\([^)]*\)|RandomForest(?:\s+Model)?)?\b/gi, "Severity Prediction")
    .replace(/\bStudent\s*B\s*(?:\([^)]*\)|DBSCAN(?:\s+Model)?)?\b/gi, "Hotspot Explorer (DBSCAN)")
    .replace(/\bStudent\s*C\s*(?:\([^)]*\)|RoadRiskGNN)?\b/gi, "Road Risk Analysis (GNN)")
    .replace(/\bRoadRiskGNN\b/g, "Road Risk Analysis (GNN)")
    .replace(/\bDBSCAN\s+Model\b/gi, "Hotspot Explorer (DBSCAN)")
    .replace(/\bStudent\s*A\b/gi, "Severity Prediction")
    .replace(/\bStudent\s*B\b/gi, "Hotspot Explorer")
    .replace(/\bStudent\s*C\b/gi, "Road Risk Analysis")
    .replace(/Road Risk Analysis\s+Road Risk Analysis(\s*\(GNN\))?/gi, "Road Risk Analysis (GNN)")
    .replace(/Hotspot Explorer\s+Hotspot Explorer(\s*\(DBSCAN\))?/gi, "Hotspot Explorer (DBSCAN)");
}

/**
 * Formats internal raw metric keys into clean human-readable table labels.
 */
export function cleanMetricLabel(metric: string): string {
  if (!metric) return "";
  const m = metric.trim();
  const knownLabels: Record<string, string> = {
    corridor_extent: "Corridor Extent",
    traffic_congestion: "Traffic Congestion",
    traffic_congestion_london_portion: "Traffic Flow (London)",
    corridor_delay: "Corridor Delay",
    active_disruptions: "Active Disruptions",
    active_disruptions_london_portion: "Disruptions (London)",
    precipitation_probability: "Rain Probability",
    atmospheric_condition: "Weather Condition",
    matched_hotspots_count: "Hotspot Clusters",
    corridor_dense_hotspots: "Hotspot Clusters",
    peak_segment_risk: "Peak Structural Risk",
    peak_structural_risk: "Peak Structural Risk",
  };
  if (knownLabels[m]) return knownLabels[m];
  return m.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Truncates text with ellipsis if it exceeds maxWidth in current font.
 */
function fitTextEllipsis(doc: jsPDF, text: string, maxWidth: number): string {
  const clean = cleanPdfText(text);
  if (doc.getTextWidth(clean) <= maxWidth) return clean;
  let s = clean;
  while (s.length > 3 && doc.getTextWidth(s + "...") > maxWidth) {
    s = s.slice(0, -1);
  }
  return s + "...";
}

/**
 * Cleans text for jsPDF helvetica rendering (ASCII / ISO-8859-1 safe)
 * and replaces internal model identifiers.
 */
export function cleanPdfText(text: string): string {
  if (!text) return "";
  return sanitizePublicModelNames(text)
    .replace(/→/g, "->")
    .replace(/←/g, "<-")
    .replace(/—/g, "--")
    .replace(/–/g, "-")
    .replace(/…/g, "...")
    .replace(/°C/g, " C")
    .replace(/°/g, " deg ")
    .replace(/±/g, "+/-")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2022\u25E6\u2023\u2043]/g, "*")
    .replace(/\u00A0/g, " ");
}

function sanitizeFilename(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 24);
}

export function exportJourneySafetyPdf(response: JourneyAnalyzeResponse): jsPDF {
  const {
    journey,
    route,
    live_context,
    historical_evidence,
    safety_assessment,
    llm_synthesis,
    provenance,
  } = response;

  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 12;
  const contentWidth = pageWidth - margin * 2;
  let y = margin;

  const checkPageBreak = (neededHeight: number): void => {
    if (y + neededHeight > pageHeight - margin - 10) {
      doc.addPage();
      y = margin + 5;
    }
  };

  const drawHeaderFooter = (currentPage: number, totalPages: number): void => {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.5);
    doc.setTextColor(120, 120, 120);

    // Running header on pages > 1
    if (currentPage > 1) {
      doc.text("Vantage -- AI-Powered Road Safety Intelligence | Corridor Assessment", margin, 8.5);
      const corridorLabel = cleanPdfText(`${journey.source} -> ${journey.destination}`);
      doc.text(
        corridorLabel.length > 46 ? `${corridorLabel.slice(0, 44)}...` : corridorLabel,
        pageWidth - margin,
        8.5,
        { align: "right" },
      );
      doc.setDrawColor(220, 225, 230);
      doc.setLineWidth(0.2);
      doc.line(margin, 10.5, pageWidth - margin, 10.5);
    }

    // Running footer on all pages
    doc.setDrawColor(220, 225, 230);
    doc.setLineWidth(0.2);
    doc.line(margin, pageHeight - 9.5, pageWidth - margin, pageHeight - 9.5);
    doc.text(
      "Vantage -- Road Safety Intelligence Platform | Multi-Source Deterministic Assessment",
      margin,
      pageHeight - 5.5,
    );
    doc.text(`Page ${currentPage} of ${totalPages}`, pageWidth - margin, pageHeight - 5.5, {
      align: "right",
    });
  };

  const renderSectionHeader = (title: string, tag?: string): void => {
    checkPageBreak(28);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(15, 23, 42); // slate-900
    doc.text(cleanPdfText(title).toUpperCase(), margin, y + 3.5);

    if (tag) {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(100, 116, 139);
      doc.text(cleanPdfText(tag), pageWidth - margin, y + 3.5, { align: "right" });
    }

    doc.setDrawColor(203, 213, 225); // slate-300
    doc.setLineWidth(0.3);
    doc.line(margin, y + 5.5, pageWidth - margin, y + 5.5);
    y += 8;
  };

  // ==============================================================================
  // 1. REPORT TITLE & STATUS HEADER
  // ==============================================================================
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(margin, y, contentWidth, 21, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.setTextColor(255, 255, 255);
  doc.text("VANTAGE -- Journey Safety Analysis", margin + 5, y + 7.5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(203, 213, 225);
  doc.text(
    "AI-Powered Multi-Source Corridor Safety & Environmental Risk Assessment",
    margin + 5,
    y + 12.5,
  );

  const formattedDate = new Date(provenance.analysis_timestamp).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.text(
    cleanPdfText(`Generated: ${formattedDate} | Status: ${safety_assessment.status.toUpperCase()}`),
    margin + 5,
    y + 17.5,
  );

  // Status badge on banner right
  const statusColor = STATUS_COLORS[safety_assessment.status] || [100, 116, 139];
  doc.setFillColor(statusColor[0], statusColor[1], statusColor[2]);
  doc.roundedRect(pageWidth - margin - 30, y + 5, 25, 5.5, 1, 1, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(6.8);
  doc.setTextColor(255, 255, 255);
  doc.text(safety_assessment.status.toUpperCase(), pageWidth - margin - 17.5, y + 8.8, {
    align: "center",
  });

  y += 24;

  // ==============================================================================
  // 2. JOURNEY DETAILS & SCOPE
  // ==============================================================================
  renderSectionHeader("1. Evaluated Journey Parameters");

  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(margin, y, contentWidth, 13, 1, 1, "FD");

  const midCol = margin + contentWidth / 2 + 4;
  const locMaxW = midCol - margin - 22; // width for origin/destination values

  doc.setFont("helvetica", "normal");
  doc.setFontSize(7.2);
  doc.setTextColor(100, 116, 139);
  doc.text("Origin:", margin + 3.5, y + 4.5);
  doc.text("Destination:", margin + 3.5, y + 9.5);

  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 23, 42);
  doc.text(fitTextEllipsis(doc, journey.source, locMaxW), margin + 20, y + 4.5);
  doc.text(fitTextEllipsis(doc, journey.destination, locMaxW), margin + 20, y + 9.5);

  doc.setFont("helvetica", "normal");
  doc.setTextColor(100, 116, 139);
  doc.text("Travel Date:", midCol, y + 4.5);
  doc.text("Departure Time:", midCol, y + 9.5);

  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 23, 42);
  doc.text(journey.travel_date, midCol + 23, y + 4.5);
  doc.text(journey.travel_time, midCol + 23, y + 9.5);

  y += 16;

  // ==============================================================================
  // 3. ROUTE SUMMARY
  // ==============================================================================
  renderSectionHeader("2. Computed Route Corridor");

  const colWidth = (contentWidth - 6) / 4;
  const metrics = [
    {
      label: "Total Distance",
      value: route.distance_km != null ? `${route.distance_km.toFixed(1)} km` : "Unavailable",
    },
    {
      label: "Estimated Duration",
      value:
        route.duration_minutes != null
          ? `${Math.round(route.duration_minutes)} min`
          : "Unavailable",
    },
    {
      label: "Routing Provider",
      value: cleanPdfText(route.provider || "OSRM (Open Source Routing)"),
    },
    {
      label: "Corridor Status",
      value: route.status.toUpperCase(),
    },
  ];

  metrics.forEach((m, idx) => {
    const boxX = margin + idx * (colWidth + 2);
    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(boxX, y, colWidth, 11, 1, 1, "FD");

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.2);
    doc.setTextColor(100, 116, 139);
    doc.text(m.label, boxX + 2.5, y + 3.8);

    doc.setFont("helvetica", "bold");
    let valFontSize = 7.5;
    doc.setFontSize(valFontSize);
    let valStr = m.value;
    while (doc.getTextWidth(valStr) > colWidth - 5 && valFontSize > 6.0) {
      valFontSize -= 0.5;
      doc.setFontSize(valFontSize);
    }
    if (doc.getTextWidth(valStr) > colWidth - 5) {
      while (valStr.length > 3 && doc.getTextWidth(valStr + "...") > colWidth - 5) {
        valStr = valStr.slice(0, -1);
      }
      valStr += "...";
    }
    doc.setTextColor(15, 23, 42);
    doc.text(valStr, boxX + 2.5, y + 8.2);
  });

  y += 14;

  // Geocoded coordinates detail
  if (route.source || route.destination) {
    const srcDisplay = route.source
      ? `Origin resolved: ${cleanPdfText(route.source.display_name)} (${route.source.latitude.toFixed(4)}, ${route.source.longitude.toFixed(4)})`
      : "Origin resolved: Coordinates unavailable";
    const dstDisplay = route.destination
      ? `Destination resolved: ${cleanPdfText(route.destination.display_name)} (${route.destination.latitude.toFixed(4)}, ${route.destination.longitude.toFixed(4)})`
      : "Destination resolved: Coordinates unavailable";

    const wrappedSrc = doc.splitTextToSize(srcDisplay, contentWidth);
    const wrappedDst = doc.splitTextToSize(dstDisplay, contentWidth);
    const neededCoordHeight = (wrappedSrc.length + wrappedDst.length) * 3 + 2;
    checkPageBreak(neededCoordHeight);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.5);
    doc.setTextColor(71, 85, 105);
    doc.text(wrappedSrc, margin, y);
    y += wrappedSrc.length * 3;

    doc.text(wrappedDst, margin, y);
    y += wrappedDst.length * 3 + 2;
  }

  // ==============================================================================
  // 4. LIVE TRAVEL CONDITIONS (Weather, Traffic, Incidents)
  // ==============================================================================
  renderSectionHeader("3. Real-Time Environmental Telemetry", "Live Telemetry Feeds");

  // Row 1: Weather (left) and Traffic (right)
  const dualColWidth = (contentWidth - 2.5) / 2;
  checkPageBreak(30);

  // Box A: Weather
  const weatherX = margin;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(weatherX, y, dualColWidth, 27, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.5);
  doc.setTextColor(15, 23, 42);
  doc.text("Atmospheric Weather", weatherX + 3, y + 4.5);

  const w = live_context.weather;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.8);
  doc.setTextColor(71, 85, 105);
  if (w && w.status !== "unavailable") {
    doc.text(`Condition: ${cleanPdfText(w.condition || "Recorded")}`, weatherX + 3, y + 8.5);
    doc.text(
      `Temperature: ${w.temperature_c != null ? `${w.temperature_c} C` : "N/A"}`,
      weatherX + 3,
      y + 12.2,
    );
    doc.text(
      `Current precipitation: ${cleanPdfText(w.precipitation_risk || "None")}`,
      weatherX + 3,
      y + 15.9,
    );
    doc.text(
      `Precipitation probability: ${w.precipitation_probability != null ? `${w.precipitation_probability}%` : "0%"}`,
      weatherX + 3,
      y + 19.6,
    );
    doc.text(
      `Wind: ${w.wind_speed_kmh != null ? `${w.wind_speed_kmh} km/h` : "N/A"} | Visibility: ${cleanPdfText(w.visibility || "Standard")}`,
      weatherX + 3,
      y + 23.3,
    );
  } else {
    doc.setTextColor(156, 163, 175);
    doc.text("Live weather telemetry unavailable for this corridor.", weatherX + 3, y + 12);
  }

  // Box B: Traffic
  const trafficX = margin + dualColWidth + 2.5;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(trafficX, y, dualColWidth, 27, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.5);
  doc.setTextColor(15, 23, 42);
  doc.text("Corridor Traffic Delay", trafficX + 3, y + 4.5);

  const tr = live_context.traffic;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.8);
  doc.setTextColor(71, 85, 105);

  const trCoverage = tr?.coverage_status || provenance.traffic_coverage_status;

  if (trCoverage === "provider_unsupported_for_geography") {
    doc.setTextColor(156, 163, 175);
    doc.text("TfL traffic feed unsupported for this geography.", trafficX + 3, y + 10);
    doc.text("TfL monitoring covers Greater London only.", trafficX + 3, y + 14);
    doc.text("No route-wide traffic clearance implied.", trafficX + 3, y + 18);
  } else if (trCoverage === "provider_failed") {
    doc.setTextColor(156, 163, 175);
    doc.text("Live traffic feed temporarily unavailable.", trafficX + 3, y + 10);
    doc.text("Upstream provider connection error.", trafficX + 3, y + 14);
  } else if (
    trCoverage === "provider_partially_supported" ||
    safety_assessment?.data_coverage?.traffic === "partial"
  ) {
    doc.text(
      `Congestion: ${cleanPdfText(tr?.congestion_level || "Moderate")} (London portion)`,
      trafficX + 3,
      y + 8.5,
    );
    doc.text(
      `Expected Delay: ${tr?.delay_minutes != null ? `${tr.delay_minutes} min` : "0 min"}`,
      trafficX + 3,
      y + 12.2,
    );
    doc.text("Coverage: Greater London portion only", trafficX + 3, y + 15.9);
    const partialDesc = [
      "TfL feed covers London portion only; outer",
      "motorway corridor is unmonitored.",
    ];
    doc.text(partialDesc, trafficX + 3, y + 19.6);
  } else if (tr && tr.status !== "unavailable") {
    doc.text(`Congestion: ${cleanPdfText(tr.congestion_level || "Normal")}`, trafficX + 3, y + 8.5);
    doc.text(
      `Expected Delay: ${tr.delay_minutes != null ? `${tr.delay_minutes} min` : "0 min"}`,
      trafficX + 3,
      y + 12.2,
    );
    const corridorText = tr.corridor_monitored
      ? `Area: ${cleanPdfText(tr.corridor_monitored)}`
      : "Area: Monitored Corridor";
    doc.text(corridorText, trafficX + 3, y + 15.9);
    const desc = tr.description
      ? doc.splitTextToSize(cleanPdfText(tr.description), dualColWidth - 6)
      : ["Normal operating flow."];
    doc.text(desc.slice(0, 2), trafficX + 3, y + 19.6);
  } else {
    doc.setTextColor(156, 163, 175);
    doc.text("Real-time traffic feed unavailable for corridor.", trafficX + 3, y + 12);
  }

  y += 29.5;

  // Row 2: Active Road Disruptions (full-width, dynamic height to eliminate text overlap)
  const incList = live_context.incidents || [];
  const incCov = live_context.incidents_coverage || provenance.incident_coverage_status;
  const isIncPartial =
    incCov === "provider_partially_supported" ||
    safety_assessment?.data_coverage?.incidents === "partial";
  const isIncUnsupported =
    incCov === "provider_unsupported_for_geography" ||
    safety_assessment?.data_coverage?.incidents === "unavailable";
  const isIncFailed = incCov === "provider_failed";

  checkPageBreak(18);

  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);

  if (incList.length === 0) {
    doc.roundedRect(margin, y, contentWidth, 12, 1, 1, "FD");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.5);
    doc.setTextColor(15, 23, 42);
    doc.text("Active Disruptions & Incidents", margin + 3, y + 4.5);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.8);
    doc.setTextColor(100, 116, 139);
    const incText = isIncUnsupported
      ? "TfL disruption data unsupported for this geography (covers Greater London only)."
      : isIncPartial
        ? "TfL disruption data covers Greater London portion only; outer corridor is unmonitored."
        : isIncFailed
          ? "TfL disruption feed temporarily unavailable (provider failed)."
          : "No active road incidents or major closures reported on corridor.";
    doc.text(incText, margin + 3, y + 8.5);
    y += 15;
  } else {
    // Dynamic height calculation based on actual incident descriptions
    interface IncidentDisplayItem {
      title: string;
      descLines: string[];
      height: number;
    }

    const items: IncidentDisplayItem[] = incList.slice(0, 3).map((inc) => {
      const title = `${inc.severity ? `[${inc.severity.toUpperCase()}] ` : ""}${cleanPdfText(inc.category || "Alert")}`;
      const descLines = doc
        .splitTextToSize(cleanPdfText(inc.description), contentWidth - 8)
        .slice(0, 2);
      const height = 4.2 + descLines.length * 3.2;
      return { title, descLines, height };
    });

    const totalBoxHeight = 7.5 + items.reduce((sum, item) => sum + item.height + 2, 0);
    checkPageBreak(totalBoxHeight + 2);

    doc.roundedRect(margin, y, contentWidth, totalBoxHeight, 1, 1, "FD");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.5);
    doc.setTextColor(15, 23, 42);
    const titleQualifier = isIncPartial ? " - London portion only; outer corridor unmonitored" : "";
    doc.text(
      `Active Disruptions & Incidents (${incList.length} reported${titleQualifier})`,
      margin + 3,
      y + 4.8,
    );

    let incY = y + 8.5;
    items.forEach((item) => {
      doc.setFont("helvetica", "bold");
      doc.setFontSize(6.8);
      doc.setTextColor(220, 38, 38);
      doc.text(`* ${item.title}`, margin + 3.5, incY);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.5);
      doc.setTextColor(71, 85, 105);
      doc.text(item.descLines, margin + 5, incY + 3.2);

      incY += item.height + 1.5;
    });

    y += totalBoxHeight + 3;
  }

  // ==============================================================================
  // 5. HISTORICAL CORRIDOR EVIDENCE (Severity Prediction, Hotspot Explorer, Road Risk)
  // ==============================================================================
  renderSectionHeader("4. Historical Empirical Corridor Evidence", "Historical Safety Baselines");

  const histCoverage = historical_evidence.coverage;
  const isCovered = histCoverage ? histCoverage.supported : true;

  checkPageBreak(28);

  const histColW = (contentWidth - 4) / 3;
  const histCardHeight = 25;

  // Box 1: Hotspot Explorer (DBSCAN)
  const sbX = margin;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(sbX, y, histColW, histCardHeight, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.2);
  doc.setTextColor(15, 23, 42);
  doc.text("Hotspot Explorer (DBSCAN)", sbX + 3, y + 4.5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.6);
  doc.setTextColor(71, 85, 105);
  if (isCovered && historical_evidence.student_b) {
    const sb = historical_evidence.student_b;
    doc.text(`Hotspot clusters on route: ${sb.hotspots_on_route}`, sbX + 3, y + 8.8);
    const radiusM = historical_evidence.matching?.corridor_radius_m || 1000;
    doc.text(`Corridor radius: ${radiusM}m`, sbX + 3, y + 12.5);

    if (sb.hotspots_on_route === 0) {
      doc.setFont("helvetica", "italic");
      doc.setTextColor(100, 116, 139);
      const zeroDisclaimer = doc.splitTextToSize(
        "No dense clusters intersect 1,000m corridor. Does not imply zero historical accidents.",
        histColW - 6,
      );
      doc.text(zeroDisclaimer, sbX + 3, y + 16.5);
    } else {
      doc.text(
        `Historical crashes in clusters: ${sb.total_historical_accidents != null ? sb.total_historical_accidents.toLocaleString() : "N/A"}`,
        sbX + 3,
        y + 16.5,
      );
      if (sb.highest_cluster_density != null) {
        doc.text(`Peak cluster density: ${sb.highest_cluster_density}`, sbX + 3, y + 20.2);
      }
    }
  } else {
    doc.setTextColor(156, 163, 175);
    doc.text("Historical coverage unavailable.", sbX + 3, y + 11);
    doc.text("Calibrated for Great Britain only.", sbX + 3, y + 15);
    doc.text("No geographic extrapolation.", sbX + 3, y + 19);
  }

  // Box 2: Road Risk Analysis (GNN)
  const scX = margin + histColW + 2;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(scX, y, histColW, histCardHeight, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.2);
  doc.setTextColor(15, 23, 42);
  doc.text("Road Risk Analysis (GNN)", scX + 3, y + 4.5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.6);
  doc.setTextColor(71, 85, 105);
  if (isCovered && historical_evidence.student_c) {
    const sc = historical_evidence.student_c;
    doc.text(`Segments evaluated: ${sc.segments_on_route}`, scX + 3, y + 8.8);
    doc.text(`Critical segments: ${sc.critical_segments_count}`, scX + 3, y + 12.5);
    doc.text(`High-risk segments: ${sc.high_risk_segments_count}`, scX + 3, y + 16.2);
    const peakText = sc.peak_gnn_risk != null ? `${sc.peak_gnn_risk.toFixed(4)} (Index)` : "N/A";
    doc.text(`Peak structural risk index: ${peakText}`, scX + 3, y + 20);
  } else {
    doc.setTextColor(156, 163, 175);
    doc.text("Historical GNN segment model", scX + 3, y + 11);
    doc.text("unavailable for corridor.", scX + 3, y + 15);
    doc.text("Calibrated for Great Britain only.", scX + 3, y + 19);
  }

  // Box 3: Severity Prediction (Collision Classifier Scope)
  const saX = margin + (histColW + 2) * 2;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(saX, y, histColW, histCardHeight, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.2);
  doc.setTextColor(15, 23, 42);
  doc.text("Severity Prediction (Scope)", saX + 3, y + 4.5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.4);
  doc.setTextColor(100, 116, 139);
  const saNotice = [
    "Severity Prediction is an individual",
    "collision classifier (Fatal/Serious/Slight)",
    "and is strictly not applicable to prospective",
    "route-wide corridor risk assessment.",
    "Excluded from route risk formula.",
  ];
  saNotice.forEach((line, idx) => {
    doc.text(line, saX + 3, y + 8.5 + idx * 3.1);
  });

  y += histCardHeight + 4;

  // ==============================================================================
  // 6. DETERMINISTIC JOURNEY SAFETY ASSESSMENT
  // ==============================================================================
  renderSectionHeader("5. Deterministic Safety Assessment", "Factor-Level Findings");

  // Invariant Banner: Composite Score is intentionally Not Assigned
  checkPageBreak(12);
  doc.setFillColor(241, 245, 249);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(margin, y, contentWidth, 9.5, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(7.2);
  doc.setTextColor(15, 23, 42);
  doc.text("Route-Wide Composite Score: NOT ASSIGNED", margin + 3.5, y + 3.8);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.5);
  doc.setTextColor(71, 85, 105);
  doc.text(
    "Overall score is strictly unassigned. Transparent factor findings are reported without ungrounded composite weighting.",
    margin + 3.5,
    y + 7.2,
  );

  y += 12;

  // Executive Assessment Summary
  if (safety_assessment.summary) {
    const wrappedSummary = doc.splitTextToSize(
      cleanPdfText(safety_assessment.summary),
      contentWidth,
    );
    checkPageBreak(wrappedSummary.length * 3.3 + 3);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.2);
    doc.setTextColor(30, 41, 59);
    doc.text(wrappedSummary, margin, y);
    y += wrappedSummary.length * 3.3 + 3;
  }

  // Key Operational & Risk Factors (Render with dynamic height and no clipping)
  if (safety_assessment.key_factors.length > 0) {
    checkPageBreak(12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.8);
    doc.setTextColor(15, 23, 42);
    doc.text("Key Operational & Safety Factors", margin, y + 2);
    y += 4.5;

    safety_assessment.key_factors.forEach((factor) => {
      const descLines = doc.splitTextToSize(cleanPdfText(factor.description), contentWidth - 24);
      const cardHeight = Math.max(11, 6.0 + descLines.length * 3.2);
      checkPageBreak(cardHeight + 2);

      doc.setFillColor(248, 250, 252);
      doc.setDrawColor(226, 232, 240);
      doc.roundedRect(margin, y, contentWidth, cardHeight, 1, 1, "FD");

      // Severity badge
      const color = SEVERITY_COLORS[factor.severity.toLowerCase()] || [100, 116, 139];
      doc.setFillColor(color[0], color[1], color[2]);
      doc.roundedRect(margin + 2.5, y + 2, 16, 4.2, 0.8, 0.8, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(5.8);
      doc.setTextColor(255, 255, 255);
      doc.text(factor.severity.toUpperCase(), margin + 10.5, y + 4.9, { align: "center" });

      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.2);
      doc.setTextColor(15, 23, 42);
      doc.text(cleanPdfText(factor.title), margin + 21, y + 4.9);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.5);
      doc.setTextColor(71, 85, 105);
      doc.text(descLines, margin + 21, y + 8.2);

      y += cardHeight + 2;
    });
  }

  // Supporting Evidence Table
  if (safety_assessment.supporting_evidence.length > 0) {
    checkPageBreak(16);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.8);
    doc.setTextColor(15, 23, 42);
    doc.text("Supporting Empirical Evidence Metrics", margin, y + 2);
    y += 4.5;

    // Header row
    doc.setFillColor(226, 232, 240);
    doc.rect(margin, y, contentWidth, 4.5, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(6.2);
    doc.setTextColor(15, 23, 42);
    doc.text("SOURCE", margin + 2, y + 3.2);
    doc.text("METRIC", margin + 40, y + 3.2);
    doc.text("VALUE", margin + 80, y + 3.2);
    doc.text("INTERPRETATION", margin + 114, y + 3.2);
    y += 5;

    safety_assessment.supporting_evidence.forEach((ev) => {
      const sourceLines = doc.splitTextToSize(cleanPdfText(ev.source), 36);
      const metricLabel = cleanMetricLabel(ev.metric);
      const metricLines = doc.splitTextToSize(metricLabel, 38);
      const valueLines = doc.splitTextToSize(cleanPdfText(ev.value), 32);
      const interpLines = doc.splitTextToSize(cleanPdfText(ev.interpretation), contentWidth - 116);

      const maxLines = Math.max(
        sourceLines.length,
        metricLines.length,
        valueLines.length,
        interpLines.length,
      );
      const rowHeight = Math.max(5.5, maxLines * 3.0 + 2.5);
      checkPageBreak(rowHeight + 1);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.2);
      doc.setTextColor(51, 65, 85);
      doc.text(sourceLines, margin + 2, y + 3);
      doc.text(metricLines, margin + 40, y + 3);

      doc.setFont("helvetica", "bold");
      doc.text(valueLines, margin + 80, y + 3);

      doc.setFont("helvetica", "normal");
      doc.text(interpLines, margin + 114, y + 3);

      doc.setDrawColor(241, 245, 249);
      doc.setLineWidth(0.2);
      doc.line(margin, y + rowHeight - 0.5, pageWidth - margin, y + rowHeight - 0.5);
      y += rowHeight;
    });
    y += 2;
  }

  // ==============================================================================
  // 7. GROUNDED GEMINI SYNTHESIS (AI-Assisted)
  // ==============================================================================
  renderSectionHeader("6. Grounded AI Synthesis", "Assisted Executive Summary");

  if (llm_synthesis.status === "available" && (llm_synthesis.headline || llm_synthesis.summary)) {
    if (llm_synthesis.headline) {
      const wrappedHeadline = doc.splitTextToSize(
        cleanPdfText(llm_synthesis.headline),
        contentWidth,
      );
      checkPageBreak(wrappedHeadline.length * 4.2 + 2);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(15, 23, 42);
      doc.text(wrappedHeadline, margin, y + 2.5);
      y += wrappedHeadline.length * 4.2 + 2;
    }

    if (llm_synthesis.summary) {
      const synthSummary = doc.splitTextToSize(cleanPdfText(llm_synthesis.summary), contentWidth);
      checkPageBreak(synthSummary.length * 3.3 + 3.5);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.2);
      doc.setTextColor(51, 65, 85);
      doc.text(synthSummary, margin, y + 1.5);
      y += synthSummary.length * 3.3 + 3.5;
    }

    // Key Findings (render dynamically without clipping)
    if (llm_synthesis.key_findings.length > 0) {
      checkPageBreak(12);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.8);
      doc.setTextColor(15, 23, 42);
      doc.text("Synthesized Key Findings", margin, y + 1.5);
      y += 4;

      llm_synthesis.key_findings.forEach((kf) => {
        const kfTitleLines = doc.splitTextToSize(cleanPdfText(kf.title), contentWidth - 24);
        const kfDesc = doc.splitTextToSize(cleanPdfText(kf.description), contentWidth - 24);
        const kfHeight = Math.max(11, 4.5 + kfTitleLines.length * 3.2 + kfDesc.length * 3.0);
        checkPageBreak(kfHeight + 2);

        doc.setFillColor(248, 250, 252);
        doc.setDrawColor(226, 232, 240);
        doc.roundedRect(margin, y, contentWidth, kfHeight, 1, 1, "FD");

        const kfColor = SEVERITY_COLORS[kf.severity.toLowerCase()] || [100, 116, 139];
        doc.setFillColor(kfColor[0], kfColor[1], kfColor[2]);
        doc.roundedRect(margin + 2.5, y + 1.8, 16, 3.8, 0.8, 0.8, "F");
        doc.setFont("helvetica", "bold");
        doc.setFontSize(5.6);
        doc.setTextColor(255, 255, 255);
        doc.text(kf.severity.toUpperCase(), margin + 10.5, y + 4.5, { align: "center" });

        doc.setFont("helvetica", "bold");
        doc.setFontSize(7);
        doc.setTextColor(15, 23, 42);
        doc.text(kfTitleLines, margin + 21, y + 4.5);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(6.4);
        doc.setTextColor(71, 85, 105);
        doc.text(kfDesc, margin + 21, y + 4.5 + kfTitleLines.length * 3.2);

        y += kfHeight + 1.8;
      });
    }

    // Actionable Recommendations (render dynamically without clipping)
    if (llm_synthesis.recommendations.length > 0) {
      checkPageBreak(12);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.8);
      doc.setTextColor(15, 23, 42);
      doc.text("Prioritized Safety Recommendations", margin, y + 1.5);
      y += 4;

      llm_synthesis.recommendations.forEach((rec, idx) => {
        const actionLines = doc.splitTextToSize(
          `${idx + 1}. ${cleanPdfText(rec.action)}`,
          contentWidth - 8,
        );
        const reasonLines = doc.splitTextToSize(
          `Rationale: ${cleanPdfText(rec.reason)}`,
          contentWidth - 8,
        );
        const recHeight = Math.max(11, 4.5 + actionLines.length * 3.2 + reasonLines.length * 3.0);
        checkPageBreak(recHeight + 2);

        doc.setFillColor(248, 250, 252);
        doc.setDrawColor(226, 232, 240);
        doc.roundedRect(margin, y, contentWidth, recHeight, 1, 1, "FD");

        doc.setFont("helvetica", "bold");
        doc.setFontSize(7);
        doc.setTextColor(15, 23, 42);
        doc.text(actionLines, margin + 3, y + 4);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(6.4);
        doc.setTextColor(71, 85, 105);
        doc.text(reasonLines, margin + 3, y + 4 + actionLines.length * 3.2);

        y += recHeight + 1.8;
      });
    }
  } else {
    checkPageBreak(12);
    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(margin, y, contentWidth, 11, 1, 1, "FD");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.2);
    doc.setTextColor(100, 116, 139);
    doc.text("AI Synthesis Unavailable", margin + 3.5, y + 4.2);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.5);
    doc.setTextColor(148, 163, 184);
    doc.text(
      "AI synthesis was not generated or provider was offline. The deterministic evaluation above remains fully authoritative.",
      margin + 3.5,
      y + 7.8,
    );
    y += 14;
  }

  // ==============================================================================
  // 8. DATA AVAILABILITY & METHODOLOGICAL LIMITATIONS (Deduplicated)
  // ==============================================================================
  renderSectionHeader("7. Data Limitations & Subsystem Constraints");

  // Deduplicate limitations and ensure canonical Severity Prediction exclusion
  const rawLimitations = [...safety_assessment.limitations, ...(llm_synthesis.limitations || [])];
  const seenLimits = new Set<string>();
  let hasSeverityExclusion = false;
  const deduplicatedLimitations: string[] = [];

  for (const lim of rawLimitations) {
    const cleanLim = cleanPdfText(lim).trim();
    if (!cleanLim) continue;

    // Check if this limitation refers to Severity Prediction individual crash scope
    if (
      /severity prediction|student a|individual collision|crash-level inputs/i.test(cleanLim) &&
      /excluded|not applicable|prospective/i.test(cleanLim)
    ) {
      if (!hasSeverityExclusion) {
        hasSeverityExclusion = true;
        deduplicatedLimitations.push(
          "Severity Prediction predicts individual collision severity from crash-level inputs and is therefore excluded from prospective route-wide corridor risk assessment.",
        );
      }
      continue;
    }

    // Deduplicate partial/unsupported TfL coverage notes
    if (/tfl.*(?:greater london|portion only|unmonitored)/i.test(cleanLim)) {
      if (seenLimits.has("tfl_partial")) continue;
      seenLimits.add("tfl_partial");
      deduplicatedLimitations.push(cleanLim);
      continue;
    }

    const normKey = cleanLim.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (!seenLimits.has(normKey)) {
      seenLimits.add(normKey);
      deduplicatedLimitations.push(cleanLim);
    }
  }

  if (!hasSeverityExclusion) {
    deduplicatedLimitations.push(
      "Severity Prediction predicts individual collision severity from crash-level inputs and is therefore excluded from prospective route-wide corridor risk assessment.",
    );
  }

  // Calculate required height for limitations box
  let totalLimLines = 0;
  const limLinesArray = deduplicatedLimitations.map((lim) => {
    const wrapped = doc.splitTextToSize(`* ${lim}`, contentWidth - 8);
    totalLimLines += wrapped.length;
    return wrapped;
  });

  const limBoxHeight = Math.max(12, totalLimLines * 3.2 + 5);
  checkPageBreak(limBoxHeight + 2);

  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(margin, y, contentWidth, limBoxHeight, 1, 1, "FD");

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.5);
  doc.setTextColor(71, 85, 105);

  let limY = y + 4.5;
  limLinesArray.forEach((wrapped) => {
    doc.text(wrapped, margin + 3.5, limY);
    limY += wrapped.length * 3.2;
  });
  y = limY + 3;

  // ==============================================================================
  // 9. DATA PROVENANCE & ARCHITECTURE VERIFICATION
  // ==============================================================================
  renderSectionHeader("8. System Architecture & Provenance");

  checkPageBreak(19);
  doc.setFillColor(241, 245, 249);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(margin, y, contentWidth, 16, 1, 1, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(6.8);
  doc.setTextColor(30, 41, 59);
  doc.text("Analytical Provenance Pipeline:", margin + 3, y + 4);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(6.3);
  doc.setTextColor(71, 85, 105);

  const provColW = contentWidth / 3;
  doc.text(
    `* Geocoding: ${provenance.route_provider ? "Nominatim (OSM)" : "Direct"}`,
    margin + 3,
    y + 7.5,
  );
  doc.text(`* Routing: ${provenance.route_provider || "OSRM"}`, margin + 3, y + 10.8);
  doc.text(`* Weather: ${provenance.weather_provider || "Open-Meteo"}`, margin + 3, y + 14.1);

  const midProvX = margin + provColW;
  const trProvText =
    provenance.traffic_coverage_status === "provider_partially_supported"
      ? `${provenance.traffic_provider || "TfL"} (London portion only)`
      : provenance.traffic_coverage_status === "provider_unsupported_for_geography"
        ? "Unsupported for geography"
        : provenance.traffic_provider || "Unavailable";

  const incProvText =
    provenance.incident_coverage_status === "provider_partially_supported"
      ? `${provenance.incident_provider || "TfL"} (London portion only)`
      : provenance.incident_coverage_status === "provider_unsupported_for_geography"
        ? "Unsupported for geography"
        : provenance.incident_provider || "Unavailable";

  doc.text(`* Traffic: ${trProvText}`, midProvX, y + 7.5);
  doc.text(`* Incidents: ${incProvText}`, midProvX, y + 10.8);
  doc.text(`* Severity Prediction: Excluded from route score`, midProvX, y + 14.1);

  const rightProvX = margin + provColW * 2;
  const sbProvText = provenance.historical_data_available
    ? `Used (${provenance.matched_hotspots_count} matched)`
    : "Unsupported for geography";
  const scProvText = provenance.historical_data_available
    ? `Used (${provenance.matched_segments_count} matched)`
    : "Unsupported for geography";

  doc.text(`* Hotspot Explorer: ${sbProvText}`, rightProvX, y + 7.5);
  doc.text(`* Road Risk Analysis: ${scProvText}`, rightProvX, y + 10.8);
  doc.text(
    `* Gemini Synthesis: ${provenance.gemini_used ? "Active" : "Unavailable"}`,
    rightProvX,
    y + 14.1,
  );

  y += 19;

  // ==============================================================================
  // FINAL PASS: DRAW HEADERS AND FOOTERS ON ALL PAGES WITH ACCURATE TOTALS
  // ==============================================================================
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    drawHeaderFooter(i, totalPages);
  }

  // ==============================================================================
  // DOWNLOAD PDF WITH DETERMINISTIC SANITIZED FILENAME
  // ==============================================================================
  const srcSlug = sanitizeFilename(journey.source);
  const dstSlug = sanitizeFilename(journey.destination);
  const dateSlug = sanitizeFilename(journey.travel_date);
  const filename = `journey-safety-analysis-${srcSlug}-to-${dstSlug}-${dateSlug}.pdf`;

  doc.save(filename);
  return doc;
}
