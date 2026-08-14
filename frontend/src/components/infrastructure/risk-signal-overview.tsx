import { MapPinned, ShieldAlert, Route as RouteIcon, Activity } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CardSkeleton } from "@/components/common/loading-skeleton";
import { PRIORITY_DISPLAY } from "@/constants/infrastructure";
import { cn } from "@/lib/utils";
import type { RiskSignal } from "@/lib/api/infrastructure";

const ICONS: LucideIcon[] = [MapPinned, ShieldAlert, RouteIcon, Activity];

export function RiskSignalOverview({
  signals,
  isLoading,
}: {
  signals: RiskSignal[];
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
      {signals.map((signal, index) => {
        const Icon = ICONS[index % ICONS.length]!;
        const display = PRIORITY_DISPLAY[signal.level];
        return (
          <Card key={signal.id} className="border-border bg-card shadow-none">
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="min-w-0 text-xs leading-snug font-bold tracking-[0.12em] text-muted-foreground uppercase">
                  {signal.label}
                </p>
                <Icon className="h-4 w-4 shrink-0 text-primary" aria-hidden />
              </div>
              <p className="text-2xl leading-tight text-foreground">{signal.value}</p>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn("font-bold", display.badgeClassName)}>
                  {display.label}
                </Badge>
                <span className="min-w-0 text-xs text-muted-foreground">{signal.note}</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
