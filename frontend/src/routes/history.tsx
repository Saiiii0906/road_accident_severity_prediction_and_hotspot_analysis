import { useCallback, useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, History as HistoryIcon, SearchX } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import { HistoryFiltersPanel } from "@/components/history/history-filters";
import { HistorySummaryCards } from "@/components/history/history-summary";
import { HistoryList } from "@/components/history/history-list";
import { HistoryDetails } from "@/components/history/history-details";
import {
  DEFAULT_HISTORY_FILTERS,
  loadHistory,
  summarizeHistory,
  type HistoryFilters,
  type HistoryRecord,
} from "@/lib/api/history";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History — Vantage" },
      {
        name: "description",
        content:
          "Review previous road-safety analyses, prediction runs and generated reports in one workspace.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "History — Vantage" },
      {
        property: "og:description",
        content:
          "Analysis history workspace: prior severity predictions, hotspot queries, risk analyses and reports.",
      },
    ],
  }),
  component: HistoryPage,
});

type Status = "idle" | "loading" | "success" | "error";

function HistoryPage() {
  const [draftFilters, setDraftFilters] = useState<HistoryFilters>(DEFAULT_HISTORY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<HistoryFilters>(DEFAULT_HISTORY_FILTERS);
  const [status, setStatus] = useState<Status>("idle");
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const run = useCallback(async (filters: HistoryFilters) => {
    setStatus("loading");
    try {
      const next = await loadHistory(filters);
      setRecords(next);
      setSelectedId((current) => (current && next.some((r) => r.id === current) ? current : null));
      setStatus("success");
    } catch {
      setRecords([]);
      setSelectedId(null);
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    void run(appliedFilters);
  }, [appliedFilters, run]);

  const handleApply = useCallback(() => {
    setAppliedFilters({ ...draftFilters });
  }, [draftFilters]);

  const handleReset = useCallback(() => {
    setDraftFilters(DEFAULT_HISTORY_FILTERS);
    setAppliedFilters(DEFAULT_HISTORY_FILTERS);
  }, []);

  const isLoading = status === "loading" || status === "idle";
  const summary = useMemo(() => summarizeHistory(records), [records]);
  const selected = records.find((r) => r.id === selectedId) ?? null;

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Workspace"
          title="History"
          description="Review previous road-safety analyses, prediction runs and generated reports."
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,320px)_minmax(0,1fr)] xl:items-start">
          <div className="space-y-6 xl:sticky xl:top-24">
            <HistoryFiltersPanel
              value={draftFilters}
              isLoading={status === "loading"}
              onChange={setDraftFilters}
              onApply={handleApply}
              onReset={handleReset}
            />
          </div>

          <div className="min-w-0 space-y-6">
            {status === "error" ? (
              <EmptyState
                icon={AlertTriangle}
                title="History unavailable"
                description="The record set could not be loaded for the selected controls."
                action={<Button onClick={() => void run(appliedFilters)}>Retry</Button>}
              />
            ) : (
              <>
                <HistorySummaryCards summary={summary} isLoading={isLoading} />

                {!isLoading && records.length === 0 ? (
                  <EmptyState
                    icon={SearchX}
                    title="No recorded analyses found"
                    description="Run a Severity Prediction, Hotspot query, Road Risk Analysis, or AI Infrastructure Report to populate your workspace history."
                    action={
                      <Button variant="outline" onClick={handleReset}>
                        Reset controls
                      </Button>
                    }
                  />
                ) : (
                  <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_minmax(0,380px)] 2xl:items-start">
                    <HistoryList
                      records={records}
                      selectedId={selectedId}
                      isLoading={isLoading}
                      onSelect={(id) => setSelectedId((current) => (current === id ? null : id))}
                    />
                    <div className="min-w-0">
                      {isLoading ? null : (
                        <HistoryDetails record={selected} onClear={() => setSelectedId(null)} />
                      )}
                    </div>
                  </div>
                )}

                {!isLoading && records.length > 0 ? (
                  <p className="flex items-center gap-2 text-sm text-muted-foreground">
                    <HistoryIcon className="h-4 w-4 shrink-0" aria-hidden />
                    Showing {records.length} recorded analysis run{records.length === 1 ? "" : "s"}{" "}
                    in your active workspace.
                  </p>
                ) : null}
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
