import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/section-header";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { HistoryRow } from "@/components/history/history-row";
import type { HistoryRecord } from "@/lib/api/history";

export function HistoryList({
  records,
  selectedId,
  isLoading,
  onSelect,
}: {
  records: HistoryRecord[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Analysis history"
          description="Chronological log of executed predictions, hotspot queries, risk profiles, and AI reports."
        />
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-5">
            <LoadingSkeleton rows={5} />
          </div>
        ) : (
          <ul className="min-w-0">
            {records.map((record) => (
              <HistoryRow
                key={record.id}
                record={record}
                isSelected={record.id === selectedId}
                onSelect={() => onSelect(record.id)}
              />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
