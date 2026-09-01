import {
  AlertTriangle,
  BrainCircuit,
  Calendar,
  CheckCircle2,
  Clock,
  Clock3,
  CloudSun,
  Cpu,
  Layers,
  MapPin,
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
        <Badge variant="outline" className="border-success/30 bg-success/10 text-success text-xs">
          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
          Active
        </Badge>
      );
    case "unavailable":
      return (
        <Badge variant="outline" className="border-destructive/30 bg-destructive/10 text-destructive text-xs">
          <AlertTriangle className="mr-1 h-3 w-3" aria-hidden="true" />
          Unavailable
        </Badge>
      );
    case "pending":
    default:
      return (
        <Badge variant="outline" className="border-warning/30 bg-warning/10 text-warning text-xs font-normal">
          <Clock3 className="mr-1 h-3 w-3" aria-hidden="true" />
          Pending Provider Integration
        </Badge>
      );
  }
}

export function JourneyResults({ response }: JourneyResultsProps) {
  const { journey, route, live_context, historical_evidence, safety_assessment, llm_synthesis, provenance } = response;

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
              <CardTitle className="text-xl font-bold text-foreground flex items-center gap-2">
                <span>{journey.source}</span>
                <span className="text-muted-foreground">→</span>
                <span>{journey.destination}</span>
              </CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1 bg-muted/60 px-2.5 py-1 rounded-md border border-border">
                <Calendar className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                {journey.travel_date}
              </span>
              <span className="inline-flex items-center gap-1 bg-muted/60 px-2.5 py-1 rounded-md border border-border">
                <Clock className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                {journey.travel_time}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          <p className="text-sm text-muted-foreground">
            {safety_assessment.summary ||
              "Journey itinerary validated. Subsystem providers will supply corridor geometry, real-time context, and ML evidence during live-data execution."}
          </p>
        </CardContent>
      </Card>

      {/* Subsystem Capabilities Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 1. Route & Corridor Geometry */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
            <div className="space-y-1">
              <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
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
            <div className="rounded-md bg-muted/40 p-3 border border-border/60 text-xs space-y-1">
              <div className="flex justify-between">
                <span>Calculated distance:</span>
                <span className="font-medium text-foreground">
                  {route.distance_km != null ? `${route.distance_km} km` : "Pending routing provider"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Estimated duration:</span>
                <span className="font-medium text-foreground">
                  {route.duration_minutes != null ? `${route.duration_minutes} min` : "Pending routing provider"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Corridor segments:</span>
                <span className="font-medium text-foreground">
                  {route.segments.length > 0 ? `${route.segments.length} segments` : "Pending road alignment"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 2. Real-Time Environmental Context */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
            <div className="space-y-1">
              <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                <CloudSun className="h-4 w-4 text-primary" aria-hidden="true" />
                Live Environmental Context
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Real-time traffic flows, ambient weather, and active hazards.
              </CardDescription>
            </div>
            <StatusBadge status={live_context.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="rounded-md bg-muted/40 p-3 border border-border/60 text-xs space-y-1">
              <div className="flex justify-between">
                <span>Traffic congestion:</span>
                <span className="font-medium text-foreground">
                  {live_context.traffic?.congestion_level || "Pending traffic feed"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Weather condition:</span>
                <span className="font-medium text-foreground">
                  {live_context.weather?.condition || "Pending weather feed"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Active incidents:</span>
                <span className="font-medium text-foreground">
                  {live_context.incidents.length > 0 ? `${live_context.incidents.length} reported` : "None reported (provider pending)"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3. Historical ML Model Evidence */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
            <div className="space-y-1">
              <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                <Cpu className="h-4 w-4 text-primary" aria-hidden="true" />
                Historical ML Grounding
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Empirical models: Student A (Severity), Student B (Hotspots), Student C (GNN).
              </CardDescription>
            </div>
            <StatusBadge status={historical_evidence.status} />
          </CardHeader>
          <CardContent className="space-y-3 pt-2 text-sm text-muted-foreground">
            <div className="rounded-md bg-muted/40 p-3 border border-border/60 text-xs space-y-1">
              <div className="flex justify-between">
                <span>Student A (RandomForest):</span>
                <span className="font-medium text-foreground">
                  {historical_evidence.student_a?.predicted_severity || "Pending route alignment"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Student B (DBSCAN Clusters):</span>
                <span className="font-medium text-foreground">
                  {historical_evidence.student_b != null
                    ? `${historical_evidence.student_b.hotspots_on_route} on route`
                    : "Pending corridor lookup"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Student C (RoadRiskGNN):</span>
                <span className="font-medium text-foreground">
                  {historical_evidence.student_c != null
                    ? `${historical_evidence.student_c.critical_segments_count} critical segments`
                    : "Pending topological scoring"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4. Gemini AI Multi-Source Synthesis */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
            <div className="space-y-1">
              <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
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
            <div className="rounded-md bg-muted/40 p-3 border border-border/60 text-xs space-y-1">
              <div className="flex justify-between">
                <span>Synthesis status:</span>
                <span className="font-medium text-foreground">
                  {llm_synthesis.summary ? "Generated" : "Pending multi-source grounding"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Actionable precautions:</span>
                <span className="font-medium text-foreground">
                  {llm_synthesis.recommendations.length > 0
                    ? `${llm_synthesis.recommendations.length} precautions`
                    : "Pending pipeline execution"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Provenance & Architecture Verification */}
      <Card className="border-border bg-muted/20 shadow-none">
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" aria-hidden="true" />
            <span>
              Analysis evaluation generated at <strong className="text-foreground">{formattedTimestamp}</strong>
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-muted border border-border">
              Routing: {provenance.route_provider || "Unconnected"}
            </span>
            <span className="px-2 py-0.5 rounded bg-muted border border-border">
              Live data: {provenance.live_data_available ? "Connected" : "Not connected"}
            </span>
            <span className="px-2 py-0.5 rounded bg-muted border border-border">
              Gemini synthesis: {provenance.gemini_used ? "Active" : "Pending"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

