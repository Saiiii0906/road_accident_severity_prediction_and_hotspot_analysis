import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PRIORITY_DISPLAY } from "@/constants/infrastructure";
import { cn } from "@/lib/utils";
import type { PriorityIntervention } from "@/lib/api/infrastructure";

export function PriorityInterventions({
  interventions,
  isLoading,
}: {
  interventions: PriorityIntervention[];
  isLoading: boolean;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Priority interventions"
          description="Ranked demonstration interventions — ordering will come from the connected model."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <LoadingSkeleton rows={5} />
        ) : interventions.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No interventions match the selected risk threshold.
          </p>
        ) : (
          <ol className="space-y-3">
            {interventions.map((item, index) => {
              const display = PRIORITY_DISPLAY[item.level];
              return (
                <li key={item.id} className="rounded-xl border border-border bg-muted/20 p-4">
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-border bg-card text-sm font-bold text-foreground">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="min-w-0 text-sm font-bold text-foreground">
                          {item.intervention}
                        </p>
                        <Badge
                          variant="outline"
                          className={cn("shrink-0 font-bold", display.badgeClassName)}
                        >
                          {display.label} priority
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1.5">
                          <span
                            className={cn("h-1.5 w-1.5 rounded-full", display.dotClassName)}
                            aria-hidden
                          />
                          {item.signal}
                        </span>
                        <span aria-hidden>·</span>
                        <span className="min-w-0">{item.location}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{item.rationale}</p>
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
