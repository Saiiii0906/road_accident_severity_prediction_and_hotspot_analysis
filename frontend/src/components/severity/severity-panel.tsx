import { AlertTriangle, Gauge, RotateCcw } from "lucide-react";
import { EmptyState } from "@/components/common/empty-state";
import { SectionHeader } from "@/components/common/section-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { CardSkeleton, LoadingSkeleton } from "@/components/common/loading-skeleton";
import { SeverityResult } from "@/components/severity/severity-result";
import type { SeverityPredictionResult } from "@/lib/api/severity";

export type SeverityStatus = "idle" | "loading" | "success" | "error";

interface SeverityPanelProps {
  status: SeverityStatus;
  result: SeverityPredictionResult | null;
  errorMessage: string | null;
  onRetry: () => void;
}

export function SeverityPanel({ status, result, errorMessage, onRetry }: SeverityPanelProps) {
  if (status === "loading") {
    return (
      <Card className="border-border bg-card shadow-none">
        <CardHeader className="border-b border-border">
          <SectionHeader
            title="Analyzing accident conditions…"
            description="The prediction service is evaluating the submitted scenario."
          />
        </CardHeader>
        <CardContent className="space-y-5 p-5 sm:p-6">
          <CardSkeleton />
          <LoadingSkeleton rows={3} />
        </CardContent>
      </Card>
    );
  }

  if (status === "error") {
    return (
      <Card className="border-border bg-card shadow-none">
        <CardContent className="p-0">
          <EmptyState
            icon={AlertTriangle}
            title="Unable to generate prediction"
            description={errorMessage ?? "Please verify the entered information and try again."}
            action={
              <Button variant="outline" onClick={onRetry}>
                <RotateCcw className="h-4 w-4" aria-hidden />
                Retry
              </Button>
            }
          />
        </CardContent>
      </Card>
    );
  }

  if (status === "success" && result) {
    return <SeverityResult result={result} />;
  }

  return (
    <Card className="border-border bg-card shadow-none">
      <CardContent className="p-0">
        <EmptyState
          icon={Gauge}
          title="No assessment yet"
          description="Enter accident conditions to generate a severity assessment."
        />
      </CardContent>
    </Card>
  );
}
