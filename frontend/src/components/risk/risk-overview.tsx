import { Gauge, Layers, Sparkles, Activity } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CardSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { RiskOverview as Overview } from "@/lib/api/risk";

const CARDS: { key: keyof Overview; label: string; icon: LucideIcon }[] = [
  { key: "overallRiskLevel", label: "Overall risk level", icon: Gauge },
  { key: "highRiskConditionCount", label: "High-risk conditions", icon: Layers },
  { key: "mostSignificantFactor", label: "Most significant factor", icon: Sparkles },
  { key: "severeAccidentRate", label: "Severe accident rate", icon: Activity },
];

export function RiskOverview({
  overview,
  isLoading,
}: {
  overview: Overview | null;
  isLoading: boolean;
}) {
  if (isLoading || !overview) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {CARDS.map((card) => (
          <CardSkeleton key={card.key} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
      {CARDS.map(({ key, label, icon: Icon }) => {
        const isLevel = key === "overallRiskLevel";
        const display = RISK_LEVEL_DISPLAY[overview.overallRiskLevel];
        return (
          <Card key={key} className="border-border bg-card shadow-none">
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="min-w-0 text-xs leading-snug font-bold tracking-[0.12em] text-muted-foreground uppercase">
                  {label}
                </p>
                <Icon className="h-4 w-4 shrink-0 text-primary" aria-hidden />
              </div>
              {isLevel ? (
                <Badge variant="outline" className={cn("font-bold", display.badgeClassName)}>
                  {display.label}
                </Badge>
              ) : (
                <p
                  className="text-xl leading-tight break-words text-foreground"
                  title={String(overview[key])}
                >
                  {overview[key]}
                </p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
