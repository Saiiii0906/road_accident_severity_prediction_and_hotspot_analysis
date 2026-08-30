import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { IMPACT_EFFORT_DISPLAY, PRIORITY_DISPLAY } from "@/constants/infrastructure";
import { cn } from "@/lib/utils";
import type { PriorityMatrixRow } from "@/lib/api/infrastructure";

export function ImplementationPriorities({
  rows,
  isLoading,
}: {
  rows: PriorityMatrixRow[];
  isLoading: boolean;
}) {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Implementation priorities"
          description="Decision matrix mapping priority level, expected safety impact, and delivery effort."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <LoadingSkeleton rows={5} />
        ) : rows.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No interventions to prioritise at this threshold.
          </p>
        ) : (
          <ul className="space-y-2.5">
            {rows.map((row) => {
              const priority = PRIORITY_DISPLAY[row.priority];
              const impact = IMPACT_EFFORT_DISPLAY[row.impact];
              const effort = IMPACT_EFFORT_DISPLAY[row.effort];
              return (
                <li
                  key={row.id}
                  className="grid min-w-0 gap-2 rounded-lg border border-border bg-muted/20 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                >
                  <p className="min-w-0 text-sm text-foreground">{row.intervention}</p>
                  <div className="flex flex-wrap items-center gap-1.5 sm:justify-end">
                    <Badge variant="outline" className={cn("font-bold", priority.badgeClassName)}>
                      {priority.label}
                    </Badge>
                    <Badge variant="outline" className={impact.className}>
                      Impact: {impact.label}
                    </Badge>
                    <Badge variant="outline" className={effort.className}>
                      Effort: {effort.label}
                    </Badge>
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
