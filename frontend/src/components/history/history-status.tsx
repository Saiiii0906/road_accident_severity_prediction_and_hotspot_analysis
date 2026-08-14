import { Badge } from "@/components/ui/badge";
import { HISTORY_STATUS_DISPLAY } from "@/constants/history";
import { cn } from "@/lib/utils";
import type { HistoryStatus as Status } from "@/lib/api/history";

export function HistoryStatusBadge({ status, className }: { status: Status; className?: string }) {
  const display = HISTORY_STATUS_DISPLAY[status];
  return (
    <Badge variant="outline" className={cn("gap-1.5 font-bold", display.badgeClassName, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", display.dotClassName)} aria-hidden />
      {display.label}
    </Badge>
  );
}
