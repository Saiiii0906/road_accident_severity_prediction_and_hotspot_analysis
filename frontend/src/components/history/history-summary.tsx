import { Layers, CircleCheck, Loader, TriangleAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { CardSkeleton } from "@/components/common/loading-skeleton";
import type { HistorySummary as Summary } from "@/lib/api/history";

const ITEMS: { key: keyof Summary; label: string; icon: LucideIcon }[] = [
  { key: "total", label: "Total analyses", icon: Layers },
  { key: "completed", label: "Completed", icon: CircleCheck },
  { key: "processing", label: "Processing", icon: Loader },
  { key: "failed", label: "Failed", icon: TriangleAlert },
];

export function HistorySummaryCards({
  summary,
  isLoading,
}: {
  summary: Summary;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {ITEMS.map(({ key, label, icon: Icon }) => (
        <Card key={key} className="border-border bg-card shadow-none">
          <CardContent className="space-y-2 p-5">
            <div className="flex items-center justify-between gap-3">
              <p className="min-w-0 text-xs leading-snug font-bold tracking-[0.12em] text-muted-foreground uppercase">
                {label}
              </p>
              <Icon className="h-4 w-4 shrink-0 text-primary" aria-hidden />
            </div>
            <p className="text-2xl leading-tight text-foreground">{summary[key]}</p>
            <small className="text-muted-foreground">Recorded in workspace</small>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
