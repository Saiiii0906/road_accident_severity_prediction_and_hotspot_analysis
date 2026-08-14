import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HistoryStatusBadge } from "@/components/history/history-status";
import { ANALYSIS_TYPE_DISPLAY } from "@/constants/history";
import { ANALYSIS_ROUTE, type HistoryRecord } from "@/lib/api/history";
import { cn } from "@/lib/utils";

export function HistoryRow({
  record,
  isSelected,
  onSelect,
}: {
  record: HistoryRecord;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const type = ANALYSIS_TYPE_DISPLAY[record.type];
  const canView = record.status === "completed";

  return (
    <li
      className={cn("min-w-0 border-b border-border last:border-b-0", isSelected && "bg-muted/40")}
    >
      <div className="grid min-w-0 gap-3 p-4 sm:p-5">
        <button
          type="button"
          onClick={onSelect}
          aria-pressed={isSelected}
          className="grid min-w-0 gap-2 text-left"
        >
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border bg-muted/40 px-2 py-1 text-xs font-bold text-muted-foreground">
              <type.icon className="h-3.5 w-3.5" aria-hidden />
              {type.label}
            </span>
            <HistoryStatusBadge status={record.status} />
          </div>
          <p className="min-w-0 text-sm font-bold text-foreground">{record.title}</p>
          <p className="min-w-0 text-sm text-muted-foreground">
            {record.regionLabel} · {record.periodLabel} · {record.createdLabel}
          </p>
          <p className="min-w-0 text-sm text-foreground">
            <span className="text-muted-foreground">Result: </span>
            {record.result}
          </p>
        </button>

        <div className="flex flex-wrap gap-2">
          {canView ? (
            <Button asChild variant="outline" size="sm">
              <Link to={ANALYSIS_ROUTE[record.type]}>
                View analysis
                <ArrowUpRight className="h-4 w-4" aria-hidden />
              </Link>
            </Button>
          ) : (
            <Button variant="outline" size="sm" disabled>
              {record.status === "processing" ? "Awaiting results" : "Unavailable"}
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onSelect}>
            {isSelected ? "Viewing details" : "Show details"}
          </Button>
        </div>
      </div>
    </li>
  );
}
