import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { FocusArea } from "@/lib/api/risk";

export function RecommendedActions({
  focusAreas,
  isLoading,
}: {
  focusAreas: FocusArea[];
  isLoading: boolean;
}) {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Recommended focus areas"
          description="Intervention-oriented presentation layer based on the demo dataset."
        />
      </CardHeader>
      <CardContent className="p-5">
        {isLoading ? (
          <LoadingSkeleton rows={4} />
        ) : focusAreas.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No focus areas available for the current analysis controls.
          </p>
        ) : (
          <ul className="space-y-3">
            {focusAreas.map((area) => {
              const display = RISK_LEVEL_DISPLAY[area.level];
              return (
                <li
                  key={area.id}
                  className="min-w-0 space-y-2 rounded-xl border border-border bg-muted/20 p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="min-w-0 truncate text-sm text-foreground">{area.area}</h3>
                    <Badge
                      variant="outline"
                      className={cn("shrink-0 font-bold", display.badgeClassName)}
                    >
                      {display.label}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-bold text-foreground">Signal — </span>
                    {area.signal}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-bold text-foreground">Suggested action — </span>
                    {area.action}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
