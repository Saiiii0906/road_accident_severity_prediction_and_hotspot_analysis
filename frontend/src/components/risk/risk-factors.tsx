import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { TableSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { RiskFactor } from "@/lib/api/risk";

export function RiskFactors({ factors, isLoading }: { factors: RiskFactor[]; isLoading: boolean }) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Key risk factors"
          description="Risk factors ranked by their relative contribution to predicted road risk."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <TableSkeleton rows={6} />
        ) : factors.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No factors available for the current analysis controls.
          </p>
        ) : (
          <ol className="divide-y divide-border">
            {[...factors]
              .sort((a, b) => b.contribution - a.contribution)
              .map((factor, index) => {
                const display = RISK_LEVEL_DISPLAY[factor.level];
                return (
                  <li key={factor.id} className="min-w-0 space-y-2 py-4 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="flex min-w-0 items-baseline gap-2">
                        <span className="shrink-0 text-xs font-bold text-muted-foreground tabular-nums">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <span className="min-w-0 truncate text-sm text-foreground">
                          {factor.label}
                        </span>
                      </span>
                      <Badge
                        variant="outline"
                        className={cn("shrink-0 font-bold", display.badgeClassName)}
                      >
                        {display.label}
                      </Badge>
                    </div>
                    <div
                      className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
                      role="img"
                      aria-label={`${factor.label}: relative contribution ${factor.contribution} of 100`}
                    >
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          display.barClassName,
                        )}
                        style={{ width: `${factor.contribution}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Relative contribution {factor.contribution}/100
                    </p>
                  </li>
                );
              })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
