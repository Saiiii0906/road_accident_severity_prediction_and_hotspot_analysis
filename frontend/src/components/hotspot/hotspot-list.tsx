import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { TableSkeleton } from "@/components/common/loading-skeleton";
import { HOTSPOT_INTENSITY_DISPLAY } from "@/constants/hotspots";
import { cn } from "@/lib/utils";
import type { Hotspot } from "@/lib/api/hotspots";

export function HotspotList({
  hotspots,
  selectedId,
  isLoading,
  onSelect,
}: {
  hotspots: Hotspot[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Ranked hotspots"
          description="Ordered by severe accident concentration in the current filter set."
        />
      </CardHeader>
      <CardContent className="p-4 sm:p-5">
        {isLoading ? (
          <TableSkeleton rows={5} />
        ) : hotspots.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No hotspots to rank for the current filters.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {[...hotspots]
              .sort((a, b) => b.severeAccidentCount - a.severeAccidentCount)
              .map((hotspot) => {
                const display = HOTSPOT_INTENSITY_DISPLAY[hotspot.intensity];
                const selected = hotspot.id === selectedId;
                return (
                  <li key={hotspot.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(hotspot.id)}
                      aria-pressed={selected}
                      className={cn(
                        "grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-lg px-2 py-3 text-left transition-colors hover:bg-muted/40",
                        selected && "bg-muted/50",
                      )}
                    >
                      <span
                        className={cn("h-2.5 w-2.5 rounded-full", display.dotClassName)}
                        aria-hidden
                      />
                      <span className="min-w-0">
                        <span className="block truncate text-sm text-foreground">
                          {hotspot.location}
                        </span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {hotspot.accidentCount.toLocaleString()} accidents ·{" "}
                          {hotspot.severeAccidentCount.toLocaleString()} severe
                        </span>
                      </span>
                      <Badge
                        variant="outline"
                        className={cn("shrink-0 font-bold", display.badgeClassName)}
                      >
                        {display.label}
                      </Badge>
                    </button>
                  </li>
                );
              })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
