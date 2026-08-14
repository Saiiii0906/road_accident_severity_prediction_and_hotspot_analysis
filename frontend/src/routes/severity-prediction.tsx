import { useCallback, useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { SeverityForm } from "@/components/severity/severity-form";
import { SeverityPanel, type SeverityStatus } from "@/components/severity/severity-panel";
import type { SeverityFormValues } from "@/components/severity/severity-schema";
import { toPredictionRequest } from "@/components/severity/severity-schema";
import { predictSeverity, type SeverityPredictionResult } from "@/lib/api/severity";
import { ApiError } from "@/lib/api/client";

export const Route = createFileRoute("/severity-prediction")({
  head: () => ({
    meta: [
      { title: "Severity Prediction — Vantage" },
      {
        name: "description",
        content:
          "Assess the expected severity of a road accident using environmental, road and traffic conditions.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Severity Prediction — Vantage" },
      {
        property: "og:description",
        content: "Estimate expected accident severity for a described collision scenario.",
      },
    ],
  }),
  component: SeverityPredictionPage,
});

function SeverityPredictionPage() {
  const [status, setStatus] = useState<SeverityStatus>("idle");
  const [result, setResult] = useState<SeverityPredictionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const lastValues = useRef<SeverityFormValues | null>(null);

  const run = useCallback(async (values: SeverityFormValues) => {
    lastValues.current = values;
    setStatus("loading");
    setErrorMessage(null);
    try {
      const prediction = await predictSeverity(toPredictionRequest(values));
      setResult(prediction);
      setStatus("success");
    } catch (error) {
      setResult(null);
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Please verify the entered information and try again.",
      );
      setStatus("error");
    }
  }, []);

  const handleRetry = useCallback(() => {
    if (lastValues.current) {
      void run(lastValues.current);
    } else {
      setStatus("idle");
    }
  }, [run]);

  const handleReset = useCallback(() => {
    lastValues.current = null;
    setResult(null);
    setErrorMessage(null);
    setStatus("idle");
  }, []);

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Modelling"
          title="Severity Prediction"
          description="Assess the expected severity of a road accident using environmental, road and traffic conditions."
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] xl:items-start">
          <SeverityForm
            isSubmitting={status === "loading"}
            onSubmit={(values) => void run(values)}
            onReset={handleReset}
          />
          <div className="xl:sticky xl:top-24">
            <SeverityPanel
              status={status}
              result={result}
              errorMessage={errorMessage}
              onRetry={handleRetry}
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
