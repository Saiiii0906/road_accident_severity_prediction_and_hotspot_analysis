import { useCallback, useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, FileText, Info } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ReportControls } from "@/components/infrastructure/report-controls";
import { ReportStatusBar } from "@/components/infrastructure/report-status";
import { RiskSignalOverview } from "@/components/infrastructure/risk-signal-overview";
import { PriorityInterventions } from "@/components/infrastructure/priority-interventions";
import { SupportingEvidence } from "@/components/infrastructure/supporting-evidence";
import { InfrastructureRecommendations } from "@/components/infrastructure/infrastructure-recommendations";
import { ImplementationPriorities } from "@/components/infrastructure/implementation-priorities";
import { ReportSummaryCard } from "@/components/infrastructure/report-summary";
import { ReportActions } from "@/components/infrastructure/report-actions";
import {
  DEFAULT_REPORT_FILTERS,
  generateInfrastructureReport,
  type InfrastructureReport,
  type ReportFilters,
} from "@/lib/api/infrastructure";

export const Route = createFileRoute("/ai-infrastructure-report")({
  head: () => ({
    meta: [
      { title: "AI Infrastructure Report — Vantage" },
      {
        name: "description",
        content:
          "Translate road-safety signals into prioritized infrastructure interventions and actionable recommendations.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "AI Infrastructure Report — Vantage" },
      {
        property: "og:description",
        content:
          "Prioritized infrastructure interventions and supporting evidence derived from road-safety risk signals.",
      },
    ],
  }),
  component: AiInfrastructureReportPage,
});

type Status = "idle" | "generating" | "success" | "error";

function AiInfrastructureReportPage() {
  const [draftFilters, setDraftFilters] = useState<ReportFilters>(DEFAULT_REPORT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>(DEFAULT_REPORT_FILTERS);
  const [status, setStatus] = useState<Status>("idle");
  const [report, setReport] = useState<InfrastructureReport | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState(false);

  const run = useCallback(async (filters: ReportFilters) => {
    setStatus("generating");
    setErrorMessage(null);
    try {
      setReport(await generateInfrastructureReport(filters));
      setStatus("success");
    } catch {
      setReport(null);
      setStatus("error");
      setErrorMessage("The report could not be compiled for the selected controls.");
    }
  }, []);

  useEffect(() => {
    void run(appliedFilters);
  }, [appliedFilters, run]);

  const handleReset = useCallback(() => {
    setExportNotice(false);
    setDraftFilters(DEFAULT_REPORT_FILTERS);
    setAppliedFilters(DEFAULT_REPORT_FILTERS);
  }, []);

  const handleGenerate = useCallback(() => {
    setExportNotice(false);
    setAppliedFilters({ ...draftFilters });
  }, [draftFilters]);

  const isLoading = status === "generating" || status === "idle";
  const isEmpty =
    status === "success" &&
    !!report &&
    report.interventions.length === 0 &&
    report.recommendations.length === 0 &&
    report.priorities.length === 0;

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Decision support"
          title="AI Infrastructure Report"
          description="Translate road-safety signals into prioritized infrastructure interventions and actionable recommendations."
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,320px)_minmax(0,1fr)] xl:items-start">
          <div className="space-y-6 xl:sticky xl:top-24">
            <ReportControls
              value={draftFilters}
              isGenerating={status === "generating"}
              onChange={setDraftFilters}
              onGenerate={handleGenerate}
              onReset={handleReset}
            />
          </div>

          <div className="min-w-0 space-y-6">
            <ReportStatusBar status={status} generatedLabel={report?.generatedLabel} />

            {exportNotice ? (
              <Alert className="border-border bg-muted/30">
                <Info className="h-4 w-4" aria-hidden />
                <AlertDescription>
                  Export is a placeholder in this phase. Document generation will be enabled once
                  backend report intelligence is connected.
                </AlertDescription>
              </Alert>
            ) : null}

            {status === "error" ? (
              <EmptyState
                icon={AlertTriangle}
                title="Report unavailable"
                description={errorMessage ?? "Something went wrong while compiling the report."}
                action={<Button onClick={() => void run(appliedFilters)}>Retry report</Button>}
              />
            ) : isEmpty ? (
              <EmptyState
                icon={FileText}
                title="No interventions at this threshold"
                description="Lower the risk threshold or widen the region and period, then generate the report again."
                action={
                  <Button variant="outline" onClick={handleReset}>
                    Reset controls
                  </Button>
                }
              />
            ) : (
              <>
                <RiskSignalOverview signals={report?.signals ?? []} isLoading={isLoading} />

                <PriorityInterventions
                  interventions={report?.interventions ?? []}
                  isLoading={isLoading}
                />

                <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
                  <SupportingEvidence evidence={report?.evidence ?? []} isLoading={isLoading} />
                  <div className="space-y-6">
                    <ReportSummaryCard summary={report?.summary ?? null} isLoading={isLoading} />
                    <ImplementationPriorities
                      rows={report?.priorities ?? []}
                      isLoading={isLoading}
                    />
                  </div>
                </div>

                <InfrastructureRecommendations
                  recommendations={report?.recommendations ?? []}
                  isLoading={isLoading}
                />
              </>
            )}

            <ReportActions
              isGenerating={status === "generating"}
              onGenerate={handleGenerate}
              onRefresh={() => {
                setExportNotice(false);
                void run(appliedFilters);
              }}
              onExport={() => setExportNotice(true)}
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
