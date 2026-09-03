import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Clock3,
  CloudSun,
  Cpu,
  Info,
  Layers,
  Lightbulb,
  Navigation,
  Route as RouteIcon,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DataAvailabilityStatus, JourneyAnalyzeResponse } from "@/lib/api/journey";

interface JourneyResultsProps {
  response: JourneyAnalyzeResponse;
}

function StatusBadge({ status }: { status: DataAvailabilityStatus }) {
  switch (status) {
    case "available":
      return (
        <Badge variant="outline" className="border-success/30 bg-success/10 text-xs text-success">
          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
          Active
        </Badge>
      );
    case "partial":
      return (
        <Badge variant="outline" className="border-primary/30 bg-primary/10 text-xs text-primary">
          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
          Partial
        </Badge>
      );
    case "unavailable":
      return (
        <Badge
          variant="outline"
          className="border-destructive/30 bg-destructive/10 text-xs text-destructive"
        >
          <AlertTriangle className="mr-1 h-3 w-3" aria-hidden="true" />
          Unavailable
        </Badge>
      );
    case "pending":
    default:
      return (
        <Badge
          variant="outline"
          className="border-warning/30 bg-warning/10 text-xs font-normal text-warning"
        >
          <Clock3 className="mr-1 h-3 w-3" aria-hidden="true" />
          Pending
        </Badge>
      );
  }
}

function SeverityBadge({ severity }: { severity: string }) {
  switch (severity.toLowerCase()) {
    case "critical":
      return (
        <Badge variant="destructive" className="text-[10px] font-semibold uppercase">
          Critical
        </Badge>
      );
    case "high":
      return (
        <Badge
          variant="outline"
          className="border-destructive/40 bg-destructive/10 text-[10px] font-semibold uppercase text-destructive"
        >
          High
        </Badge>
      );
    case "moderate":
      return (
        <Badge
          variant="outline"
          className="border-warning/40 bg-warning/10 text-[10px] font-semibold uppercase text-warning"
        >
          Moderate
        </Badge>
      );
    case "low":
      return (
        <Badge
          variant="outline"
          className="border-success/40 bg-success/10 text-[10px] font-semibold uppercase text-success"
        >
          Low
        </Badge>
      );
    case "advisory":
    case "informational":
    default:
      return (
        <Badge variant="secondary" className="text-[10px] font-normal uppercase">
          {severity}
        </Badge>
      );
  }
}

export function JourneyResults({ response }: JourneyResultsProps) {
  const {
    journey,
    route,
    live_context,
    historical_evidence,
    safety_assessment,
    llm_synthesis,
    provenance,
  } = response;

  const formattedTimestamp = new Date(provenance.analysis_timestamp).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <div className="space-y-6">
      {/* Journey Itinerary Header */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                <Navigation className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                Evaluated Journey Scope
              </div>
              <CardTitle className="flex items-center gap-2 text-xl font-bold text-foreground">
                <span>{journey.source}</span>
                <span className="text-muted-foreground">→</span>
                <span>{journey.destination}</span>
              </CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="flex items-center gap-1.5 px-2.5 py-1 text-xs">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
                <span>{journey.travel_date}</span>
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-1.5 px-2.5 py-1 text-xs">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
                <span>{journey.travel_time}</span>
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 1. Primary: Deterministic Journey Safety Assessment (Phase 4D) */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 border-b border-border pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <CardTitle className="flex items-center gap-2 text-lg font-bold text-foreground">
                <ShieldAlert className="h-5 w-5 text-primary" aria-hidden="true" />
                Deterministic Journey Safety Assessment
              </CardTitle>
              {safety_assessment.level && (
                <Badge variant="outline" className="text-xs font-semibold">
                  {safety_assessment.level}
                </Badge>
              )}
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Evidence-based evaluation grounded in real routing, live environmental feeds, and
              empirical models without arbitrary weighting.
            </CardDescription>
          </div>
          <StatusBadge status={safety_assessment.status} />
        </CardHeader>

        <CardContent className="space-y-5 pt-4">
          {/* Executive Summary */}
          <div className="rounded-md border border-border/70 bg-muted/30 p-3 text-xs text-foreground">
            <p className="leading-relaxed">
              {safety_assessment.summary ||
                "Deterministic safety assessment pending multi-source evidence computation."}
            </p>
          </div>

          {/* Key Risk & Operational Factors */}
          {safety_assessment.key_factors.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Key Operational & Risk Factors
              </h4>
              <div className="grid gap-3 sm:grid-cols-2">
                {safety_assessment.key_factors.map((factor, idx) => (
                  <div
                    key={`${factor.factor}-${idx}`}
                    className="space-y-1.5 rounded-md border border-border/50 bg-background/60 p-3 text-xs shadow-xs"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-foreground">{factor.title}</span>
                      <SeverityBadge severity={factor.severity} />
                    </div>
                    <p className="text-muted-foreground leading-snug">{factor.description}</p>
                    <div className="pt-1 text-[10px] text-muted-foreground/80">
                      Source: <span className="font-medium text-foreground">{factor.source}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Supporting Evidence Metrics */}
          {safety_assessment.supporting_evidence.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Supporting Empirical Evidence
              </h4>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {safety_assessment.supporting_evidence.map((ev, idx) => (
                  <div
                    key={`${ev.metric}-${idx}`}
                    className="rounded-md border border-border/40 bg-muted/20 p-2.5 text-xs"
                  >
                    <div className="flex items-center justify-between font-medium text-foreground">
                      <span className="truncate">{ev.source}</span>
                      <span className="text-primary font-semibold">{ev.value}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground leading-tight">
                      {ev.interpretation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Subsystem Coverage & Limitations */}
          <div className="space-y-2.5 border-t border-border/40 pt-4">
            {safety_assessment.data_coverage && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-muted-foreground font-medium">Data Coverage:</span>
                <span className="rounded border border-border bg-muted/50 px-2 py-0.5 text-[11px]">
                  Route:{" "}
                  <strong className="text-foreground">
                    {safety_assessment.data_coverage.route}
                  </strong>
                </span>
                <span className="rounded border border-border bg-muted/50 px-2 py-0.5 text-[11px]">
                  Weather:{" "}
                  <strong className="text-foreground">
                    {safety_assessment.data_coverage.weather}
                  </strong>
                </span>
                <span className="rounded border border-border bg-muted/50 px-2 py-0.5 text-[11px]">
                  Traffic:{" "}
                  <strong className="text-foreground">
                    {safety_assessment.data_coverage.traffic}
                  </strong>
                </span>
                <span className="rounded border border-border bg-muted/50 px-2 py-0.5 text-[11px]">
                  Disruptions:{" "}
                  <strong className="text-foreground">
                    {safety_assessment.data_coverage.incidents}
                  </strong>
                </span>
                <span className="rounded border border-border bg-muted/50 px-2 py-0.5 text-[11px]">
                  Historical:{" "}
                  <strong className="text-foreground">
                    {safety_assessment.data_coverage.historical}
                  </strong>
                </span>
              </div>
            )}

            {safety_assessment.limitations.length > 0 && (
              <div className="space-y-1 rounded border border-border/30 bg-muted/10 p-2 text-[11px] text-muted-foreground">
                <div className="flex items-center gap-1.5 font-medium text-foreground">
                  <Info className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                  <span>Methodological Constraints & Data Limitations</span>
                </div>
                <ul className="list-inside list-disc space-y-0.5 pl-1">
                  {safety_assessment.limitations.map((lim, idx) => (
                    <li key={idx} className="leading-tight">
                      {lim}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2. Secondary: Grounded Gemini Journey Safety Synthesis (Phase 4E) */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 border-b border-border pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <CardTitle className="flex items-center gap-2 text-lg font-bold text-foreground">
                <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
                Journey Safety Summary
              </CardTitle>
              <Badge variant="secondary" className="text-xs font-normal">
                Grounded AI Synthesis
              </Badge>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Explainable narrative synthesis and actionable driver guidance strictly synthesized
              from verified telemetry.
            </CardDescription>
          </div>
          <StatusBadge status={llm_synthesis.status} />
        </CardHeader>

        <CardContent className="space-y-5 pt-4">
          {llm_synthesis.status === "unavailable" ? (
            <div className="rounded-md border border-destructive/20 bg-destructive/5 p-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-2 font-medium text-destructive">
                <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                <span>AI Narrative Synthesis Unavailable</span>
              </div>
              <p className="mt-1">
                Grounded AI synthesis is currently unavailable for this itinerary. The deterministic
                safety assessment and evidentiary metrics above remain fully active and
                authoritative.
              </p>
              {llm_synthesis.limitations.length > 0 && (
                <ul className="mt-2 list-inside list-disc space-y-0.5 text-[11px]">
                  {llm_synthesis.limitations.map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <>
              {/* Headline & Summary */}
              {llm_synthesis.headline && (
                <h3 className="text-sm font-bold text-foreground">{llm_synthesis.headline}</h3>
              )}
              <div className="rounded-md border border-border/70 bg-muted/20 p-3.5 text-xs text-foreground">
                <p className="leading-relaxed">
                  {llm_synthesis.summary ||
                    "AI narrative synthesis will summarize verified conditions upon pipeline execution."}
                </p>
              </div>

              {/* Key Findings */}
              {llm_synthesis.key_findings.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Key Synthesized Findings
                  </h4>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {llm_synthesis.key_findings.map((kf, idx) => (
                      <div
                        key={idx}
                        className="space-y-1.5 rounded-md border border-border/50 bg-background/60 p-3 text-xs shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-foreground">{kf.title}</span>
                          <SeverityBadge severity={kf.severity} />
                        </div>
                        <p className="text-muted-foreground leading-snug">{kf.description}</p>
                        {kf.evidence_sources.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1 pt-1 text-[10px] text-muted-foreground">
                            <span>Evidence:</span>
                            {kf.evidence_sources.map((src, sIdx) => (
                              <Badge
                                key={sIdx}
                                variant="outline"
                                className="px-1.5 py-0 text-[9px]"
                              >
                                {src}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actionable Recommendations */}
              {llm_synthesis.recommendations.length > 0 && (
                <div className="space-y-3">
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Lightbulb className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    <span>Actionable Precautions & Guidance</span>
                  </h4>
                  <div className="space-y-2">
                    {llm_synthesis.recommendations.map((rec, idx) => (
                      <div
                        key={idx}
                        className="space-y-1 rounded-md border border-border/40 bg-muted/15 p-3 text-xs"
                      >
                        <div className="font-semibold text-foreground">
                          {idx + 1}. {rec.action}
                        </div>
                        <p className="text-muted-foreground leading-tight">{rec.reason}</p>
                        {rec.evidence_sources.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1 pt-1 text-[10px] text-muted-foreground">
                            <span>Grounding:</span>
                            {rec.evidence_sources.map((src, sIdx) => (
                              <Badge
                                key={sIdx}
                                variant="outline"
                                className="px-1.5 py-0 text-[9px]"
                              >
                                {src}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclosures & Limitations */}
              {llm_synthesis.limitations.length > 0 && (
                <div className="space-y-1 rounded border border-border/30 bg-muted/10 p-2 text-[11px] text-muted-foreground">
                  <div className="flex items-center gap-1.5 font-medium text-foreground">
                    <Info className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    <span>Synthesis Disclosures & Boundary Limitations</span>
                  </div>
                  <ul className="list-inside list-disc space-y-0.5 pl-1">
                    {llm_synthesis.limitations.map((lim, idx) => (
                      <li key={idx} className="leading-tight">
                        {lim}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Subsystem Capabilities Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 1. Route & Corridor Geometry */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
                <RouteIcon className="h-4 w-4 text-primary" aria-hidden="true" />
                Route & Corridor Geometry
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Topological traversal and corridor segment alignment.
              </CardDescription>
            </div>
            <StatusBadge status={route.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="space-y-2 rounded-md border border-border/60 bg-muted/40 p-3 text-xs">
              <div className="flex justify-between">
                <span>Routing engine:</span>
                <span className="font-medium text-foreground">
                  {route.provider || "Pending integration"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Calculated distance:</span>
                <span className="font-medium text-foreground">
                  {route.distance_km != null
                    ? `${route.distance_km} km`
                    : "Pending routing provider"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Estimated duration:</span>
                <span className="font-medium text-foreground">
                  {route.duration_minutes != null
                    ? `${route.duration_minutes} min`
                    : "Pending routing provider"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Route geometry:</span>
                <span className="font-medium text-foreground">
                  {route.geometry?.coordinates?.length
                    ? `${route.geometry.coordinates.length} coordinate waypoints`
                    : "Pending geometry"}
                </span>
              </div>
              {route.source?.display_name && (
                <div className="border-t border-border/40 pt-1.5">
                  <span className="text-muted-foreground">Resolved origin: </span>
                  <span className="line-clamp-1 font-medium text-foreground">
                    {route.source.display_name} ({route.source.latitude.toFixed(4)},{" "}
                    {route.source.longitude.toFixed(4)})
                  </span>
                </div>
              )}
              {route.destination?.display_name && (
                <div className="pt-1">
                  <span className="text-muted-foreground">Resolved destination: </span>
                  <span className="line-clamp-1 font-medium text-foreground">
                    {route.destination.display_name} ({route.destination.latitude.toFixed(4)},{" "}
                    {route.destination.longitude.toFixed(4)})
                  </span>
                </div>
              )}
              {route.segments.length > 0 && (
                <div className="border-t border-border/40 pt-1.5">
                  <span className="text-muted-foreground">Corridor roads: </span>
                  <span className="font-medium text-foreground">
                    {route.segments
                      .map((s) => s.name)
                      .filter(Boolean)
                      .slice(0, 4)
                      .join(" → ")}
                    {route.segments.length > 4 ? ` (+${route.segments.length - 4} more)` : ""}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 2. Real-Time Environmental Context */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
                <CloudSun className="h-4 w-4 text-primary" aria-hidden="true" />
                Live Environmental Context
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Real atmospheric conditions, corridor congestion, and active disruptions.
              </CardDescription>
            </div>
            <StatusBadge status={live_context.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="space-y-2.5 rounded-md border border-border/60 bg-muted/40 p-3 text-xs">
              {/* Weather Subsystem */}
              <div className="space-y-1">
                <div className="flex items-center justify-between font-medium text-foreground">
                  <span>Weather ({live_context.providers?.weather || "Open-Meteo"}):</span>
                  <span className="font-semibold text-primary">
                    {live_context.weather?.condition || "Unavailable"}
                  </span>
                </div>
                {live_context.weather?.temperature_c != null && (
                  <div className="grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                    <span>Temp: {live_context.weather.temperature_c}°C</span>
                    <span>Rain prob: {live_context.weather.precipitation_probability ?? 0}%</span>
                    <span>Wind: {live_context.weather.wind_speed_kmh ?? 0} km/h</span>
                    <span>Visibility: {live_context.weather.visibility ?? "Good"}</span>
                  </div>
                )}
              </div>

              {/* Traffic Subsystem */}
              <div className="space-y-1 border-t border-border/40 pt-2">
                <div className="flex items-center justify-between font-medium text-foreground">
                  <span>Traffic ({live_context.providers?.traffic || "TfL"}):</span>
                  <span className="capitalize text-foreground">
                    {live_context.traffic?.congestion_level || "Unavailable"}
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {live_context.traffic?.description || "No monitored corridor data available."}
                </p>
              </div>

              {/* Incidents Subsystem */}
              <div className="space-y-1 border-t border-border/40 pt-2">
                <div className="flex items-center justify-between font-medium text-foreground">
                  <span>Active Disruptions:</span>
                  <span>
                    {live_context.incidents.length > 0
                      ? `${live_context.incidents.length} on corridor`
                      : "None detected"}
                  </span>
                </div>
                {live_context.incidents.length > 0 && (
                  <div className="space-y-1 pt-1">
                    {live_context.incidents.slice(0, 3).map((inc) => (
                      <div
                        key={inc.incident_id}
                        className="rounded border border-border/30 bg-background/50 p-1.5 text-[11px]"
                      >
                        <div className="flex items-center justify-between gap-1 font-medium text-foreground">
                          <span className="truncate">{inc.category || "Works"}</span>
                          <span className="text-[10px] text-muted-foreground">{inc.severity}</span>
                        </div>
                        <p className="line-clamp-1 text-muted-foreground">{inc.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3. Historical ML Model Evidence */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
                <Cpu className="h-4 w-4 text-primary" aria-hidden="true" />
                Historical ML Grounding
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Empirical models: Student B (DBSCAN Hotspots) & Student C (GNN Network Risk).
              </CardDescription>
            </div>
            <StatusBadge status={historical_evidence.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="space-y-2.5 rounded-md border border-border/60 bg-muted/40 p-3 text-xs">
              {/* Coverage & Metadata Header */}
              <div className="flex items-center justify-between border-b border-border/40 pb-1.5">
                <span className="text-muted-foreground">Geographic Scope:</span>
                <span className="font-medium text-foreground">
                  {historical_evidence.coverage?.region || "Great Britain (UK)"} (
                  {historical_evidence.matching?.corridor_radius_m
                    ? `${historical_evidence.matching.corridor_radius_m}m buffer`
                    : "1,000m buffer"}
                  )
                </span>
              </div>

              {/* Student B Hotspots */}
              <div className="space-y-1">
                <div className="flex items-center justify-between font-medium text-foreground">
                  <span>Student B (DBSCAN Hotspots):</span>
                  <span className="text-primary font-semibold">
                    {historical_evidence.student_b != null
                      ? `${historical_evidence.student_b.hotspots_on_route} on corridor`
                      : "Pending"}
                  </span>
                </div>
                {historical_evidence.student_b &&
                  historical_evidence.student_b.hotspots_on_route > 0 && (
                    <div className="space-y-1 pt-1 text-[11px]">
                      <div className="text-muted-foreground">
                        Total corridor historical crashes:{" "}
                        <strong className="text-foreground">
                          {historical_evidence.student_b.total_historical_accidents?.toLocaleString() ??
                            "N/A"}
                        </strong>
                        {historical_evidence.student_b.highest_cluster_density != null && (
                          <span>
                            {" "}
                            (Peak density: {historical_evidence.student_b.highest_cluster_density})
                          </span>
                        )}
                      </div>
                      {historical_evidence.student_b.matched_hotspots.slice(0, 2).map((h) => (
                        <div
                          key={h.cluster_id}
                          className="rounded border border-border/30 bg-background/50 p-1 text-[11px]"
                        >
                          <div className="flex justify-between font-medium text-foreground">
                            <span>Cluster #{h.cluster_id}</span>
                            <span>{h.total_accidents} crashes</span>
                          </div>
                          <div className="flex justify-between text-muted-foreground">
                            <span>
                              {h.dominant_severity} • {h.dominant_road_type}
                            </span>
                            <span>{Math.round(h.distance_to_route_m)}m from route</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
              </div>

              {/* Student C GNN Risk */}
              <div className="space-y-1 border-t border-border/40 pt-2">
                <div className="flex items-center justify-between font-medium text-foreground">
                  <span>Student C (RoadRiskGNN):</span>
                  <span className="text-primary font-semibold">
                    {historical_evidence.student_c != null
                      ? `${historical_evidence.student_c.segments_on_route} segments`
                      : "Pending"}
                  </span>
                </div>
                {historical_evidence.student_c &&
                  historical_evidence.student_c.segments_on_route > 0 && (
                    <div className="space-y-1 pt-1 text-[11px]">
                      <div className="flex justify-between text-muted-foreground">
                        <span>
                          Critical:{" "}
                          <strong className="text-destructive">
                            {historical_evidence.student_c.critical_segments_count}
                          </strong>
                          {" • "}
                          High:{" "}
                          <strong className="text-warning">
                            {historical_evidence.student_c.high_risk_segments_count}
                          </strong>
                        </span>
                        <span>
                          Peak risk:{" "}
                          <strong className="text-foreground">
                            {historical_evidence.student_c.peak_gnn_risk != null
                              ? `${Math.round(historical_evidence.student_c.peak_gnn_risk * 100)}%`
                              : "N/A"}
                          </strong>
                        </span>
                      </div>
                      {historical_evidence.student_c.matched_segments.slice(0, 2).map((s) => (
                        <div
                          key={s.edge_id}
                          className="rounded border border-border/30 bg-background/50 p-1 text-[11px]"
                        >
                          <div className="flex justify-between font-medium text-foreground">
                            <span>Road A{s.road_number}</span>
                            <span
                              className={
                                s.risk_category === "Critical"
                                  ? "text-destructive font-semibold"
                                  : s.risk_category === "High"
                                    ? "text-warning font-semibold"
                                    : "text-foreground"
                              }
                            >
                              {Math.round(s.predicted_risk * 100)}% ({s.risk_category})
                            </span>
                          </div>
                          <div className="text-muted-foreground">
                            {Math.round(s.distance_to_route_m)}m from route
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
              </div>

              {/* Student A Note */}
              <div className="border-t border-border/40 pt-2 text-[10px] text-muted-foreground">
                <span>Student A (Severity): </span>
                <span>
                  Individual collision model — not applicable to prospective route corridor
                  traversal.
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4. Grounded AI Synthesis Summary */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
                Gemini Multi-Source Synthesis
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Explainable decision support and actionable safety recommendations.
              </CardDescription>
            </div>
            <StatusBadge status={llm_synthesis.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="space-y-1 rounded-md border border-border/60 bg-muted/40 p-3 text-xs">
              <div className="flex justify-between">
                <span>Synthesis status:</span>
                <span className="font-medium text-foreground">
                  {llm_synthesis.status === "available"
                    ? "Active"
                    : llm_synthesis.status === "partial"
                      ? "Partial Context"
                      : llm_synthesis.status === "unavailable"
                        ? "Unavailable"
                        : "Pending"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Actionable precautions:</span>
                <span className="font-medium text-foreground">
                  {llm_synthesis.recommendations.length > 0
                    ? `${llm_synthesis.recommendations.length} precautions`
                    : "None generated"}
                </span>
              </div>
              {llm_synthesis.headline && (
                <div className="border-t border-border/40 pt-1.5 text-foreground font-medium">
                  {llm_synthesis.headline}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Provenance & Architecture Verification */}
      <Card className="border-border bg-muted/20 shadow-none">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" aria-hidden="true" />
            <span>
              Analysis evaluation generated at{" "}
              <strong className="text-foreground">{formattedTimestamp}</strong>
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Routing: {provenance.route_provider || "Unconnected"}
            </span>
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Weather: {provenance.weather_provider || "Unconnected"}
            </span>
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Traffic: {provenance.traffic_provider || "Unconnected"}
            </span>
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Incidents: {provenance.incident_provider || "Unconnected"}
            </span>
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Historical:{" "}
              {provenance.historical_data_available
                ? `Connected (${provenance.matched_hotspots_count} hotspots, ${provenance.matched_segments_count} segments)`
                : "Unavailable"}
            </span>
            <span className="rounded border border-border bg-muted px-2 py-0.5">
              Gemini synthesis: {provenance.gemini_used ? "Active" : "Unavailable/Pending"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
