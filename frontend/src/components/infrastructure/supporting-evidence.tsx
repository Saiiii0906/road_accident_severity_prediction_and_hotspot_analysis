import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PRIORITY_DISPLAY } from "@/constants/infrastructure";
import { cn } from "@/lib/utils";
import type { EvidenceItem } from "@/lib/api/infrastructure";

export function SupportingEvidence({
  evidence,
  isLoading,
}: {
  evidence: EvidenceItem[];
  isLoading: boolean;
}) {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Supporting evidence"
          description="Demo signals that would normally underpin an intervention decision."
        />
      </CardHeader>
      <CardContent className="p-5 sm:p-6">
        {isLoading ? (
          <LoadingSkeleton rows={5} />
        ) : evidence.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No supporting signals available for this scope.
          </p>
        ) : (
          <ul className="space-y-4">
            {evidence.map((item) => {
              const display = PRIORITY_DISPLAY[item.level];
              return (
                <li key={item.id} className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="min-w-0 text-sm font-bold text-foreground">{item.signal}</p>
                    <Badge
                      variant="outline"
                      className={cn("shrink-0 font-bold", display.badgeClassName)}
                    >
                      {item.value}
                    </Badge>
                  </div>
                  <div
                    className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
                    role="img"
                    aria-label={`${item.signal} demo strength ${item.strength} of 100`}
                  >
                    <div
                      className={cn("h-full rounded-full", display.barClassName)}
                      style={{ width: `${item.strength}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">{item.relation}</p>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
