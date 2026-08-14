import { useCallback, useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, BarChart3 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import { RiskFilters } from "@/components/risk/risk-filters";
import { RiskOverview } from "@/components/risk/risk-overview";
import { RiskDistribution } from "@/components/risk/risk-distribution";
import { ConditionBreakdownCard } from "@/components/risk/condition-breakdown";
import { TimeAnalysis } from "@/components/risk/time-analysis";
import { RiskFactors } from "@/components/risk/risk-factors";
import { PriorityInsights } from "@/components/risk/priority-insights";
import { RecommendedActions } from "@/components/risk/recommended-actions";
import {
  DEFAULT_RISK_FILTERS,
  loadRiskAnalysis,
  type RiskAnalysis,
  type RiskFilters as Filters,
} from "@/lib/api/risk";

export const Route = createFileRoute("/road-risk-analysis")({
  head: () => ({
    meta: [
      { title: "Road Risk Analysis — Vantage" },
      {
        name: "description",
        content:
          "Analyze the road, environmental and temporal conditions associated with elevated accident risk.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Road Risk Analysis — Vantage" },
      {
        property: "og:description",
        content:
          "Understand which road, weather and time-of-day conditions are associated with elevated accident risk.",
      },
    ],
  }),
  component: RoadRiskAnalysisPage,
});

type Status = "idle" | "loading" | "success" | "error";

function RoadRiskAnalysisPage() {
  const [draftFilters, setDraftFilters] = useState<Filters>(DEFAULT_RISK_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<Filters>(DEFAULT_RISK_FILTERS);
  const [status, setStatus] = useState<Status>("idle");
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const run = useCallback(async (filters: Filters) => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      setAnalysis(await loadRiskAnalysis(filters));
      setStatus("success");
    } catch {
      setAnalysis(null);
      setStatus("error");
      setErrorMessage("The risk analysis could not be loaded for these controls.");
    }
  }, []);

  useEffect(() => {
    void run(appliedFilters);
  }, [appliedFilters, run]);

  const handleReset = useCallback(() => {
    setDraftFilters(DEFAULT_RISK_FILTERS);
    setAppliedFilters(DEFAULT_RISK_FILTERS);
  }, []);

  const isLoading = status === "loading" || status === "idle";
  const isEmpty =
    status === "success" &&
    !!analysis &&
    analysis.distribution.length === 0 &&
    analysis.roadConditions.length === 0 &&
    analysis.weatherConditions.length === 0 &&
    analysis.timeBuckets.length === 0;

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Condition profiling"
          title="Road Risk Analysis"
          description="Analyze the road, environmental and temporal conditions associated with elevated accident risk."
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,320px)_minmax(0,1fr)] xl:items-start">
          <div className="space-y-6 xl:sticky xl:top-24">
            <RiskFilters
              value={draftFilters}
              isLoading={status === "loading"}
              onChange={setDraftFilters}
              onApply={() => setAppliedFilters({ ...draftFilters })}
              onReset={handleReset}
            />
          </div>

          <div className="min-w-0 space-y-6">
            {status === "error" ? (
              <EmptyState
                icon={AlertTriangle}
                title="Analysis unavailable"
                description={errorMessage ?? "Something went wrong while analysing conditions."}
                action={<Button onClick={() => void run(appliedFilters)}>Retry analysis</Button>}
              />
            ) : isEmpty ? (
              <EmptyState
                icon={BarChart3}
                title="No conditions match these controls"
                description="Widen the region, period or condition selection and apply the analysis again."
                action={
                  <Button variant="outline" onClick={handleReset}>
                    Reset controls
                  </Button>
                }
              />
            ) : (
              <>
                <RiskOverview overview={analysis?.overview ?? null} isLoading={isLoading} />

                <RiskDistribution
                  distribution={analysis?.distribution ?? []}
                  isLoading={isLoading}
                />

                <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
                  <ConditionBreakdownCard
                    title="Road condition analysis"
                    description="Comparative risk index across recorded road-surface conditions."
                    conditions={analysis?.roadConditions ?? []}
                    isLoading={isLoading}
                    emptyMessage="No road conditions match the current analysis controls."
                  />
                  <ConditionBreakdownCard
                    title="Weather analysis"
                    description="Comparative risk index across recorded environmental conditions."
                    conditions={analysis?.weatherConditions ?? []}
                    isLoading={isLoading}
                    emptyMessage="No weather conditions match the current analysis controls."
                  />
                </div>

                <TimeAnalysis buckets={analysis?.timeBuckets ?? []} isLoading={isLoading} />

                <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
                  <RiskFactors factors={analysis?.factors ?? []} isLoading={isLoading} />
                  <div className="space-y-6">
                    <PriorityInsights insights={analysis?.insights ?? []} isLoading={isLoading} />
                    <RecommendedActions
                      focusAreas={analysis?.focusAreas ?? []}
                      isLoading={isLoading}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
