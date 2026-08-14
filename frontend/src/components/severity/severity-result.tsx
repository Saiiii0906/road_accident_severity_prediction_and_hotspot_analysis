import { ArrowUpRight, Lightbulb, ListChecks } from "lucide-react";
import { SectionHeader } from "@/components/common/section-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { SEVERITY_DISPLAY } from "@/constants/severity";
import type { SeverityPredictionResult } from "@/lib/api/severity";
import { cn } from "@/lib/utils";

function toPercent(value: number) {
  return Math.round(Math.min(Math.max(value, 0), 1) * 100);
}

export function SeverityResult({ result }: { result: SeverityPredictionResult }) {
  const display = SEVERITY_DISPLAY[result.severity];
  const probabilities = result.probabilities
    ? (Object.entries(result.probabilities) as [keyof typeof SEVERITY_DISPLAY, number][])
    : [];

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Severity assessment"
          description="Returned by the prediction service for the submitted conditions."
        />
      </CardHeader>
      <CardContent className="space-y-6 p-5 sm:p-6">
        <div
          className={cn(
            "flex flex-wrap items-end justify-between gap-4 rounded-xl border p-5",
            display.className,
          )}
        >
          <div className="min-w-0 space-y-1">
            <p className="text-xs font-bold tracking-[0.18em] uppercase opacity-80">
              Predicted severity
            </p>
            <p className="text-3xl leading-none">{display.label}</p>
            <p className="text-sm opacity-90">{display.description}</p>
          </div>
          {result.confidence !== undefined ? (
            <div className="text-right">
              <p className="text-xs font-bold tracking-wide uppercase opacity-80">Confidence</p>
              <p className="text-2xl leading-none">{toPercent(result.confidence)}%</p>
            </div>
          ) : null}
        </div>

        {probabilities.length > 0 ? (
          <div className="space-y-3">
            <h3 className="text-sm text-foreground">Class probabilities</h3>
            {probabilities.map(([level, value]) => (
              <div key={level} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{SEVERITY_DISPLAY[level].label}</span>
                  <span>{toPercent(value)}%</span>
                </div>
                <Progress value={toPercent(value)} className="h-1.5" />
              </div>
            ))}
          </div>
        ) : null}

        {result.interpretation ? (
          <div className="rounded-xl border border-border bg-muted/20 p-4">
            <div className="flex items-start gap-3">
              <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
              <div className="min-w-0 space-y-1">
                <h3 className="text-sm text-foreground">Interpretation</h3>
                <p className="text-sm text-muted-foreground">{result.interpretation}</p>
              </div>
            </div>
          </div>
        ) : null}

        {result.contributingFactors && result.contributingFactors.length > 0 ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-primary" aria-hidden />
              <h3 className="text-sm text-foreground">Key contributing factors</h3>
            </div>
            <ul className="space-y-2">
              {result.contributingFactors.map((factor) => (
                <li
                  key={factor.label}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/20 px-4 py-3"
                >
                  <span className="min-w-0 truncate text-sm text-foreground">{factor.label}</span>
                  <span className="flex shrink-0 items-center gap-2">
                    {factor.direction ? (
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {factor.direction === "increases" ? "Increases risk" : "Reduces risk"}
                      </Badge>
                    ) : null}
                    {factor.weight !== undefined ? (
                      <span className="text-xs text-muted-foreground">
                        {toPercent(factor.weight)}%
                      </span>
                    ) : null}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {result.recommendedAction ? (
          <div className="rounded-xl border border-border bg-muted/20 p-4">
            <div className="flex items-start gap-3">
              <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
              <div className="min-w-0 space-y-1">
                <h3 className="text-sm text-foreground">Recommended next action</h3>
                <p className="text-sm text-muted-foreground">{result.recommendedAction}</p>
              </div>
            </div>
          </div>
        ) : null}

        {result.modelVersion ? (
          <p className="text-xs text-muted-foreground">Model {result.modelVersion}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
