import { MousePointerClick, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { EmptyState } from "@/components/common/empty-state";
import { SectionHeader } from "@/components/common/section-header";
import { HOTSPOT_INTENSITY_DISPLAY } from "@/constants/hotspots";
import { cn } from "@/lib/utils";
import type { Hotspot } from "@/lib/api/hotspots";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 py-2.5">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-right text-sm text-foreground">{value}</dd>
    </div>
  );
}

export function HotspotDetails({
  hotspot,
  onClear,
}: {
  hotspot: Hotspot | null;
  onClear: () => void;
}) {
  if (!hotspot) {
    return (
      <Card className="border-border bg-card shadow-none">
        <CardContent className="p-0">
          <EmptyState
            icon={MousePointerClick}
            title="No hotspot selected"
            description="Select a marker on the map to review its concentration profile and recommended intervention."
          />
        </CardContent>
      </Card>
    );
  }

  const display = HOTSPOT_INTENSITY_DISPLAY[hotspot.intensity];
  const severeShare = hotspot.accidentCount
    ? Math.round((hotspot.severeAccidentCount / hotspot.accidentCount) * 100)
    : 0;

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Selected hotspot"
          description="Empirical cluster profile from Student B DBSCAN spatial analysis."
          action={
            <Button variant="ghost" size="icon" onClick={onClear} aria-label="Clear selection">
              <X className="h-4 w-4" aria-hidden />
            </Button>
          }
        />
      </CardHeader>
      <CardContent className="space-y-4 p-5 sm:p-6">
        <div className="space-y-2">
          <h3 className="text-base text-foreground">{hotspot.location}</h3>
          <Badge variant="outline" className={cn("font-bold", display.badgeClassName)}>
            {display.label} intensity
          </Badge>
        </div>

        <Separator />

        <dl className="divide-y divide-border">
          <Row label="Hotspot severity" value={display.label} />
          <Row label="Accident count" value={hotspot.accidentCount.toLocaleString()} />
          <Row
            label="Severe accidents"
            value={`${hotspot.severeAccidentCount.toLocaleString()} (${severeShare}%)`}
          />
          <Row label="Risk level" value={hotspot.riskLevel} />
        </dl>

        <div className="space-y-2">
          <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
            Dominant conditions
          </p>
          <div className="flex flex-wrap gap-2">
            {hotspot.dominantConditions.map((condition) => (
              <Badge key={condition} variant="secondary" className="font-medium">
                {condition}
              </Badge>
            ))}
          </div>
        </div>

        <div className="space-y-2 rounded-xl border border-border bg-muted/20 p-4">
          <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
            Recommended intervention
          </p>
          <p className="text-sm text-foreground">{hotspot.recommendedIntervention}</p>
        </div>
      </CardContent>
    </Card>
  );
}
