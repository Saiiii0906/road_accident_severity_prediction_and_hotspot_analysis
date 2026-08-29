import { AlertTriangle, Info, ShieldAlert, Lightbulb } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import { cn } from "@/lib/utils";
import type { PriorityInsight, RiskLevel } from "@/lib/api/risk";

const ICONS: Record<RiskLevel, LucideIcon> = {
  low: Info,
  moderate: Lightbulb,
  high: AlertTriangle,
  critical: ShieldAlert,
};

export function PriorityInsights({
  insights,
  isLoading,
}: {
  insights: PriorityInsight[];
  isLoading: boolean;
}) {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Priority insights"
          description="Priority insights derived from the connected road risk model."
        />
      </CardHeader>
      <CardContent className="p-5">
        {isLoading ? (
          <LoadingSkeleton rows={4} />
        ) : insights.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No insights available for the current analysis controls.
          </p>
        ) : (
          <ul className="space-y-3">
            {insights.map((insight) => {
              const display = RISK_LEVEL_DISPLAY[insight.level];
              const Icon = ICONS[insight.level];
              return (
                <li
                  key={insight.id}
                  className="flex items-start gap-3 rounded-xl border border-border bg-muted/20 p-4 transition-colors duration-300 hover:bg-muted/40"
                >
                  <Icon
                    className={cn(
                      "mt-0.5 h-4 w-4 shrink-0",
                      display.dotClassName.replace("bg-", "text-"),
                    )}
                    aria-hidden
                  />
                  <div className="min-w-0 space-y-2">
                    <p className="text-sm text-foreground">{insight.text}</p>
                    <Badge
                      variant="outline"
                      className={cn("text-[10px] tracking-wide uppercase", display.badgeClassName)}
                    >
                      {display.label}
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
