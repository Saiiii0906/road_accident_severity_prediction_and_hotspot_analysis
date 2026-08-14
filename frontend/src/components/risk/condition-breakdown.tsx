import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { ChartSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { ConditionBreakdown as Breakdown } from "@/lib/api/risk";

/**
 * Shared comparative presentation used by both the road-condition and weather
 * analysis sections. Values come from the isolated demo dataset.
 */
export function ConditionBreakdownCard({
  title,
  description,
  conditions,
  isLoading,
  emptyMessage,
}: {
  title: string;
  description: string;
  conditions: Breakdown[];
  isLoading: boolean;
  emptyMessage: string;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader title={title} description={description} />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <ChartSkeleton />
        ) : conditions.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <ul className="divide-y divide-border">
            {[...conditions]
              .sort((a, b) => b.riskIndex - a.riskIndex)
              .map((condition) => {
                const display = RISK_LEVEL_DISPLAY[condition.level];
                return (
                  <li key={condition.id} className="min-w-0 space-y-2 py-4 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="min-w-0 truncate text-sm text-foreground">
                        {condition.label}
                      </span>
                      <Badge
                        variant="outline"
                        className={cn("shrink-0 font-bold", display.badgeClassName)}
                      >
                        {display.label}
                      </Badge>
                    </div>
                    <div
                      className="h-2 w-full overflow-hidden rounded-full bg-muted"
                      role="img"
                      aria-label={`${condition.label}: relative risk index ${condition.riskIndex} of 100`}
                    >
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          display.barClassName,
                        )}
                        style={{ width: `${condition.riskIndex}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Risk index {condition.riskIndex} · {condition.accidentShare}% of demo records
                      — {condition.note}
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
