import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { ChartSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { TimeBucket } from "@/lib/api/risk";

export function TimeAnalysis({
  buckets,
  isLoading,
}: {
  buckets: TimeBucket[];
  isLoading: boolean;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Time-of-day analysis"
          description="Relative risk index across daily periods in the demo record set."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <ChartSkeleton />
        ) : buckets.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No periods match the current analysis controls.
          </p>
        ) : (
          <div className="space-y-5">
            <div
              className="flex h-[180px] items-end gap-2 sm:gap-3"
              role="img"
              aria-label="Relative risk index by time of day"
            >
              {buckets.map((bucket) => {
                const display = RISK_LEVEL_DISPLAY[bucket.level];
                return (
                  <div
                    key={bucket.id}
                    className="flex h-full min-w-0 flex-1 flex-col justify-end gap-2"
                  >
                    <span className="text-center text-[11px] text-muted-foreground">
                      {bucket.riskIndex}
                    </span>
                    <div
                      className={cn(
                        "w-full rounded-t-md opacity-80 transition-all duration-500",
                        display.barClassName,
                      )}
                      style={{ height: `${bucket.riskIndex}%` }}
                    />
                  </div>
                );
              })}
            </div>

            <ul className="divide-y divide-border border-t border-border">
              {buckets.map((bucket) => {
                const display = RISK_LEVEL_DISPLAY[bucket.level];
                return (
                  <li
                    key={bucket.id}
                    className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 py-2.5"
                  >
                    <span
                      className={cn("h-2.5 w-2.5 rounded-full", display.dotClassName)}
                      aria-hidden
                    />
                    <span className="min-w-0 truncate text-sm text-foreground">{bucket.label}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {bucket.severeShare}% severe share
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
