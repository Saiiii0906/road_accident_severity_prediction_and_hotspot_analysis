import { useState } from "react";
import { AlertTriangle, Minus, Plus, RotateCcw, MapPinned } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { EmptyState } from "@/components/common/empty-state";
import { MapSkeleton } from "@/components/common/loading-skeleton";
import { SectionHeader } from "@/components/common/section-header";
import { HotspotLegend } from "@/components/hotspot/hotspot-legend";
import { HOTSPOT_INTENSITY_DISPLAY } from "@/constants/hotspots";
import { cn } from "@/lib/utils";
import type { Hotspot } from "@/lib/api/hotspots";

/**
 * Map workspace shell.
 *
 * INTEGRATION BOUNDARY: the surface below is a neutral schematic canvas, not a
 * geographic projection — marker positions come from normalised cluster
 * coordinates. When Leaflet is introduced, replace only the inner surface
 * (`<div data-map-surface>`) with the map instance and keep this chrome:
 * header, zoom controls, legend and selection callbacks.
 */

const MIN_ZOOM = 1;
const MAX_ZOOM = 2.5;
const RADIUS: Record<Hotspot["intensity"], number> = {
  low: 9,
  moderate: 12,
  high: 16,
  critical: 20,
};

interface HotspotMapProps {
  hotspots: Hotspot[];
  selectedId: string | null;
  status: "idle" | "loading" | "success" | "error";
  errorMessage: string | null;
  onSelect: (id: string) => void;
  onRetry: () => void;
}

export function HotspotMap({
  hotspots,
  selectedId,
  status,
  errorMessage,
  onSelect,
  onRetry,
}: HotspotMapProps) {
  const [zoom, setZoom] = useState(1);
  const clamp = (value: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));

  return (
    <Card className="overflow-hidden border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Hotspot map"
          description="Schematic concentration view — geographic map layer connects in the integration pass."
          action={
            <Badge variant="outline" className="font-bold">
              {hotspots.length} shown
            </Badge>
          }
        />
      </CardHeader>

      <CardContent className="space-y-4 p-4 sm:p-5">
        {status === "loading" ? (
          <MapSkeleton />
        ) : status === "error" ? (
          <EmptyState
            icon={AlertTriangle}
            title="Unable to load hotspots"
            description={errorMessage ?? "Please adjust the filters and try again."}
            action={
              <Button variant="outline" onClick={onRetry}>
                <RotateCcw className="h-4 w-4" aria-hidden />
                Retry
              </Button>
            }
          />
        ) : hotspots.length === 0 ? (
          <EmptyState
            icon={MapPinned}
            title="No hotspots match these filters"
            description="Widen the region, period or condition filters to see concentration patterns."
          />
        ) : (
          <div className="relative overflow-hidden rounded-xl border border-border bg-muted/20">
            <div data-map-surface className="relative min-h-[360px] w-full lg:min-h-[460px]">
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="xMidYMid slice"
                className="absolute inset-0 h-full w-full"
                role="img"
                aria-label="Schematic hotspot concentration map"
              >
                <g style={{ transformOrigin: "50px 50px" }} transform={`scale(${zoom})`}>
                  <g className="text-border" stroke="currentColor" strokeWidth={0.15}>
                    {Array.from({ length: 9 }).map((_, i) => (
                      <line key={`v${i}`} x1={(i + 1) * 10} y1={0} x2={(i + 1) * 10} y2={100} />
                    ))}
                    {Array.from({ length: 9 }).map((_, i) => (
                      <line key={`h${i}`} x1={0} y1={(i + 1) * 10} x2={100} y2={(i + 1) * 10} />
                    ))}
                  </g>
                  <g
                    className="text-muted-foreground/40"
                    stroke="currentColor"
                    strokeWidth={1.1}
                    fill="none"
                    strokeLinecap="round"
                  >
                    <path d="M4 22 H96" />
                    <path d="M52 4 V96" />
                    <path d="M8 78 C 30 66, 46 88, 92 62" />
                    <path d="M18 6 C 22 40, 40 52, 84 58" />
                  </g>
                </g>
              </svg>

              <div
                className="absolute inset-0"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center center" }}
              >
                {hotspots.map((hotspot) => {
                  const display = HOTSPOT_INTENSITY_DISPLAY[hotspot.intensity];
                  const selected = hotspot.id === selectedId;
                  const size = RADIUS[hotspot.intensity] * 2;
                  return (
                    <button
                      key={hotspot.id}
                      type="button"
                      onClick={() => onSelect(hotspot.id)}
                      aria-pressed={selected}
                      title={`${hotspot.location} — ${display.label} intensity`}
                      className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full transition-transform duration-200 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none hover:scale-110"
                      style={{ left: `${hotspot.x * 100}%`, top: `${hotspot.y * 100}%` }}
                    >
                      <span
                        className={cn("block rounded-full opacity-25", display.dotClassName)}
                        style={{ width: size, height: size }}
                        aria-hidden
                      />
                      <span
                        className={cn(
                          "absolute top-1/2 left-1/2 block -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card",
                          display.dotClassName,
                          selected && "ring-2 ring-ring ring-offset-2 ring-offset-card",
                        )}
                        style={{ width: size / 2.4, height: size / 2.4 }}
                        aria-hidden
                      />
                      <span className="sr-only">
                        {hotspot.location}, {display.label} intensity
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="absolute top-3 right-3 flex flex-col gap-1.5">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 bg-card/95"
                  onClick={() => setZoom((z) => clamp(z + 0.25))}
                  disabled={zoom >= MAX_ZOOM}
                  aria-label="Zoom in"
                >
                  <Plus className="h-4 w-4" aria-hidden />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 bg-card/95"
                  onClick={() => setZoom((z) => clamp(z - 0.25))}
                  disabled={zoom <= MIN_ZOOM}
                  aria-label="Zoom out"
                >
                  <Minus className="h-4 w-4" aria-hidden />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 bg-card/95"
                  onClick={() => setZoom(1)}
                  aria-label="Reset zoom"
                >
                  <RotateCcw className="h-4 w-4" aria-hidden />
                </Button>
              </div>
            </div>
          </div>
        )}

        <HotspotLegend />
      </CardContent>
    </Card>
  );
}
