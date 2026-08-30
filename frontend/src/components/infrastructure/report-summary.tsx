import { Target, Wrench, Radar, ArrowRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import type { ReportSummary as Summary } from "@/lib/api/infrastructure";

export function ReportSummaryCard({
  summary,
  isLoading,
}: {
  summary: Summary | null;
  isLoading: boolean;
}) {
  const rows: { icon: LucideIcon; label: string; value: string }[] = summary
    ? [
        { icon: Target, label: "Main risk theme", value: summary.theme },
        { icon: Wrench, label: "Highest-priority intervention", value: summary.topIntervention },
        { icon: Radar, label: "Most relevant signal", value: summary.keySignal },
        { icon: ArrowRight, label: "Suggested next step", value: summary.nextStep },
      ]
    : [];

  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Infrastructure priority summary"
          description="Executive briefing synthesized from connected models."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading || !summary ? (
          <LoadingSkeleton rows={4} />
        ) : (
          <dl className="space-y-4">
            {rows.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex min-w-0 items-start gap-3">
                <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-border bg-muted/30">
                  <Icon className="h-4 w-4 text-primary" aria-hidden />
                </span>
                <div className="min-w-0">
                  <dt className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
                    {label}
                  </dt>
                  <dd className="text-sm text-foreground">{value}</dd>
                </div>
              </div>
            ))}
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
