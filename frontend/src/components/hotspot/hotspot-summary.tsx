import { MapPinned, AlertTriangle, Activity, Crosshair } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { CardSkeleton } from "@/components/common/loading-skeleton";
import type { HotspotSummary as Summary } from "@/lib/api/hotspots";

const CARDS: { key: keyof Summary; label: string; icon: LucideIcon }[] = [
  { key: "totalHotspots", label: "Total hotspots", icon: MapPinned },
  { key: "highRiskHotspots", label: "High-risk hotspots", icon: AlertTriangle },
  { key: "severeConcentration", label: "Severe accident concentration", icon: Activity },
  { key: "mostAffectedArea", label: "Most affected area", icon: Crosshair },
];

export function HotspotSummary({
  summary,
  isLoading,
}: {
  summary: Summary | null;
  isLoading: boolean;
}) {
  if (isLoading || !summary) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {CARDS.map((card) => (
          <CardSkeleton key={card.key} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
      {CARDS.map(({ key, label, icon: Icon }) => (
        <Card key={key} className="border-border bg-card shadow-none">
          <CardContent className="space-y-3 p-5">
            <div className="flex items-center justify-between gap-3">
              <p className="min-w-0 text-xs leading-snug font-bold tracking-[0.12em] text-muted-foreground uppercase">
                {label}
              </p>
              <Icon className="h-4 w-4 shrink-0 text-primary" aria-hidden />
            </div>
            <p
              className="text-xl leading-tight break-words text-foreground"
              title={String(summary[key])}
            >
              {summary[key]}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
