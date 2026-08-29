import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { ChartSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { RiskDistributionSlice } from "@/lib/api/risk";

export function RiskDistribution({
  distribution,
  isLoading,
}: {
  distribution: RiskDistributionSlice[];
  isLoading: boolean;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Risk distribution"
          description="Distribution of road segments across predicted risk bands."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <ChartSkeleton />
        ) : distribution.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No risk bands match the current analysis controls.
          </p>
        ) : (
          <ul className="space-y-5">
            {distribution.map((slice) => {
              const display = RISK_LEVEL_DISPLAY[slice.level];
              return (
                <li key={slice.level} className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="flex min-w-0 items-center gap-2 text-sm text-foreground">
                      <span
                        className={cn("h-2.5 w-2.5 shrink-0 rounded-full", display.dotClassName)}
                        aria-hidden
                      />
                      <span className="truncate">{display.label}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {slice.share}% · {slice.recordCount.toLocaleString()} records
                    </span>
                  </div>
                  <div
                    className="h-2 w-full overflow-hidden rounded-full bg-muted"
                    role="img"
                    aria-label={`${display.label}: ${slice.share} percent of road segments`}
                  >
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        display.barClassName,
                      )}
                      style={{ width: `${slice.share}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
