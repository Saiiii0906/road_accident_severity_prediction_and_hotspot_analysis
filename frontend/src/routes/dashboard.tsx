import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertCircle, Navigation } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { JourneyForm } from "@/components/journey/journey-form";
import { JourneyResults } from "@/components/journey/journey-results";
import { analyzeJourney, type JourneyAnalyzeRequest, type JourneyAnalyzeResponse } from "@/lib/api/journey";
import { recordAnalysisHistory } from "@/lib/api/history";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Journey Safety Analysis — Vantage Road Safety Intelligence" },
      {
        name: "description",
        content:
          "Multi-source journey safety evaluation combining route corridor analysis, historical ML models, and grounded AI synthesis.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Journey Safety Analysis — Vantage" },
      {
        property: "og:description",
        content: "Multi-source journey safety evaluation for planned travel itineraries.",
      },
    ],
  }),
  component: JourneySafetyDashboard,
});

function JourneySafetyDashboard() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<JourneyAnalyzeResponse | null>(null);

  const handleAnalyze = async (data: JourneyAnalyzeRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await analyzeJourney(data);
      setResponse(result);

      // Record successful journey execution in local history
      recordAnalysisHistory({
        type: "journey_safety_analysis",
        title: `${data.source} → ${data.destination}`,
        region: "all",
        regionLabel: "Corridor Analysis",
        period: data.travel_date,
        periodLabel: `${data.travel_date} ${data.travel_time}`,
        status: "completed",
        result: `Journey safety analysis evaluated for ${data.source} → ${data.destination}`,
        signals: [
          `Origin: ${data.source}`,
          `Destination: ${data.destination}`,
          `Schedule: ${data.travel_date} at ${data.travel_time}`,
        ],
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to execute journey analysis.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Multi-Source Safety Intelligence"
          title="Journey Safety Analysis"
          description="Evaluate road corridor safety, historical accident patterns, and environmental risks for your planned route and departure time."
        />

        {/* Primary Input Form */}
        <section aria-label="Journey parameters">
          <JourneyForm isLoading={isLoading} onSubmit={handleAnalyze} />
        </section>

        {/* Error Feedback */}
        {error && (
          <Alert variant="destructive" className="border-destructive/40 bg-destructive/10">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Analysis Request Failed</AlertTitle>
            <AlertDescription className="text-sm">{error}</AlertDescription>
          </Alert>
        )}

        {/* Results Panel */}
        <section aria-label="Analysis results">
          {response ? (
            <JourneyResults response={response} />
          ) : (
            <Card className="border-border bg-card shadow-none">
              <CardContent className="p-8">
                <EmptyState
                  icon={Navigation}
                  title="Ready for journey analysis"
                  description="Enter your origin, destination, departure date, and time above to initiate a corridor safety evaluation."
                />
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </AppShell>
  );
}
