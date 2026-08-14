import { Link } from "@tanstack/react-router";
import { ArrowUpRight, MousePointerClick, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { EmptyState } from "@/components/common/empty-state";
import { SectionHeader } from "@/components/common/section-header";
import { HistoryStatusBadge } from "@/components/history/history-status";
import { ANALYSIS_TYPE_DISPLAY } from "@/constants/history";
import { ANALYSIS_ROUTE, type HistoryRecord } from "@/lib/api/history";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 py-2.5">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-right text-sm text-foreground">{value}</dd>
    </div>
  );
}

export function HistoryDetails({
  record,
  onClear,
}: {
  record: HistoryRecord | null;
  onClear: () => void;
}) {
  if (!record) {
    return (
      <Card className="border-border bg-card shadow-none">
        <CardContent className="p-0">
          <EmptyState
            icon={MousePointerClick}
            title="No analysis selected"
            description="Select a record from the history list to review its scope, status and supporting signals."
          />
        </CardContent>
      </Card>
    );
  }

  const type = ANALYSIS_TYPE_DISPLAY[record.type];

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Analysis details"
          description="Illustrative record detail for review."
          action={
            <Button variant="ghost" size="icon" onClick={onClear} aria-label="Clear selection">
              <X className="h-4 w-4" aria-hidden />
            </Button>
          }
        />
      </CardHeader>
      <CardContent className="space-y-4 p-5 sm:p-6">
        <dl className="divide-y divide-border">
          <Row label="Analysis type" value={type.label} />
          <Row label="Analysis name" value={record.title} />
          <Row label="Region" value={record.regionLabel} />
          <Row label="Analysis period" value={record.periodLabel} />
          <Row label="Created" value={record.createdLabel} />
          <Row label="Status" value={<HistoryStatusBadge status={record.status} />} />
          <Row label="Result" value={record.result} />
        </dl>

        <Separator />

        <div className="space-y-3">
          <h3 className="text-sm font-bold text-foreground">Supporting signals</h3>
          <ul className="space-y-2">
            {record.signals.map((signal) => (
              <li
                key={signal}
                className="flex min-w-0 items-start gap-2 text-sm text-muted-foreground"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
                <span className="min-w-0">{signal}</span>
              </li>
            ))}
          </ul>
        </div>

        {record.status === "completed" ? (
          <Button asChild className="w-full">
            <Link to={ANALYSIS_ROUTE[record.type]}>
              View analysis
              <ArrowUpRight className="h-4 w-4" aria-hidden />
            </Link>
          </Button>
        ) : (
          <p className="text-sm text-muted-foreground">
            {record.status === "processing"
              ? "This run is still processing, so no result is available for review yet."
              : "This run failed, so no result is available for review."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
