import { useCallback, useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { HotspotFilters } from "@/components/hotspot/hotspot-filters";
import { HotspotMap } from "@/components/hotspot/hotspot-map";
import { HotspotDetails } from "@/components/hotspot/hotspot-details";
import { HotspotSummary } from "@/components/hotspot/hotspot-summary";
import { HotspotList } from "@/components/hotspot/hotspot-list";
import {
  DEFAULT_HOTSPOT_FILTERS,
  loadHotspots,
  type HotspotDataset,
  type HotspotFilters as Filters,
} from "@/lib/api/hotspots";
import { recordAnalysisHistory } from "@/lib/api/history";

export const Route = createFileRoute("/hotspot-explorer")({
  head: () => ({
    meta: [
      { title: "Hotspot Explorer — Vantage" },
      {
        name: "description",
        content:
          "Explore historical accident clusters, spatial density and priority intervention zones.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Hotspot Explorer — Vantage" },
      {
        property: "og:description",
        content:
          "Interactive map and cluster analytics for accident hotspots across the UK road network.",
      },
    ],
  }),
  component: HotspotExplorerPage,
});

type Status = "idle" | "loading" | "success" | "error";

function HotspotExplorerPage() {
  const [draftFilters, setDraftFilters] = useState<Filters>(DEFAULT_HOTSPOT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<Filters>(DEFAULT_HOTSPOT_FILTERS);
  const [status, setStatus] = useState<Status>("idle");
  const [dataset, setDataset] = useState<HotspotDataset | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const run = useCallback(async (filters: Filters) => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const next = await loadHotspots(filters);
      setDataset(next);
      setSelectedId((current) =>
        current && next.hotspots.some((h) => h.id === current) ? current : null,
      );
      setStatus("success");
      recordAnalysisHistory({
        type: "hotspot_analysis",
        title: `DBSCAN Hotspot Analysis (${filters.region.toUpperCase()})`,
        region: filters.region,
        regionLabel: filters.region === "all" ? "All UK Network" : filters.region.toUpperCase(),
        period: filters.period,
        periodLabel: filters.period === "all" ? "All Periods" : filters.period,
        status: "completed",
        result: `Identified ${next.summary.totalHotspots} clusters (${next.summary.highRiskHotspots} high risk)`,
        signals: next.hotspots
          .slice(0, 3)
          .map((h) => `${h.location}: ${h.accidentCount} accidents`),
      });
    } catch {
      setDataset(null);
      setStatus("error");
      setErrorMessage("The hotspot analysis could not be loaded for these filters.");
    }
  }, []);

  useEffect(() => {
    void run(appliedFilters);
  }, [appliedFilters, run]);

  const handleReset = useCallback(() => {
    setDraftFilters(DEFAULT_HOTSPOT_FILTERS);
    setAppliedFilters(DEFAULT_HOTSPOT_FILTERS);
    setSelectedId(null);
  }, []);

  const hotspots = dataset?.hotspots ?? [];
  const selected = hotspots.find((h) => h.id === selectedId) ?? null;
  const isLoading = status === "loading";

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Spatial analysis"
          title="Hotspot Explorer"
          description="Explore accident concentration patterns and identify locations requiring targeted road-safety intervention."
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,320px)_minmax(0,1fr)] xl:items-start">
          <div className="space-y-6 xl:sticky xl:top-24">
            <HotspotFilters
              value={draftFilters}
              isLoading={isLoading}
              onChange={setDraftFilters}
              onApply={() => setAppliedFilters({ ...draftFilters })}
              onReset={handleReset}
            />
          </div>

          <div className="min-w-0 space-y-6">
            <HotspotMap
              hotspots={hotspots}
              selectedId={selectedId}
              status={status}
              errorMessage={errorMessage}
              onSelect={setSelectedId}
              onRetry={() => void run(appliedFilters)}
            />

            <HotspotSummary summary={dataset?.summary ?? null} isLoading={isLoading} />

            <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
              <HotspotList
                hotspots={hotspots}
                selectedId={selectedId}
                isLoading={isLoading}
                onSelect={setSelectedId}
              />
              <HotspotDetails hotspot={selected} onClear={() => setSelectedId(null)} />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
