import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PRIORITY_DISPLAY } from "@/constants/infrastructure";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/lib/api/infrastructure";

export function InfrastructureRecommendations({
  recommendations,
  isLoading,
}: {
  recommendations: Recommendation[];
  isLoading: boolean;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Infrastructure recommendations"
          description="Evidence-grounded policy and engineering recommendations generated from connected models."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <LoadingSkeleton rows={4} />
        ) : recommendations.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No recommendations match the selected risk threshold.
          </p>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {recommendations.map((item) => {
              const display = PRIORITY_DISPLAY[item.level];
              return (
                <article
                  key={item.id}
                  className="min-w-0 space-y-3 rounded-xl border border-border bg-muted/20 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <h3 className="min-w-0 text-sm font-bold text-foreground">{item.title}</h3>
                    <Badge
                      variant="outline"
                      className={cn("shrink-0 font-bold", display.badgeClassName)}
                    >
                      {display.label}
                    </Badge>
                  </div>

                  <div className="space-y-1">
                    <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
                      Why it matters
                    </p>
                    <p className="text-sm text-muted-foreground">{item.why}</p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
                      Safety objective
                    </p>
                    <p className="text-sm text-muted-foreground">{item.objective}</p>
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {item.supportingSignals.map((signal) => (
                      <Badge
                        key={signal}
                        variant="outline"
                        className="border-border text-muted-foreground"
                      >
                        {signal}
                      </Badge>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
