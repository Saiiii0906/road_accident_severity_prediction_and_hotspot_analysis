import { CircleDashed, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export type ReportStatus = "idle" | "generating" | "success" | "error";

const CONFIG: Record<
  ReportStatus,
  { label: string; detail: string; className: string; spin?: boolean; icon: typeof CircleDashed }
> = {
  idle: {
    label: "Ready for analysis",
    detail: "Choose a scope and focus, then generate the report.",
    className: "border-border bg-muted/40 text-muted-foreground",
    icon: CircleDashed,
  },
  generating: {
    label: "Generating report",
    detail: "Compiling risk signals into infrastructure priorities…",
    className: "border-primary/30 bg-primary/10 text-primary",
    spin: true,
    icon: Loader2,
  },
  success: {
    label: "Analysis generated",
    detail: "Report generated from connected road-safety models and Gemini analysis.",
    className: "border-success/30 bg-success/10 text-success",
    icon: CheckCircle2,
  },
  error: {
    label: "Report unavailable",
    detail: "The report could not be compiled for the selected controls.",
    className: "border-danger/30 bg-danger/10 text-danger",
    icon: AlertTriangle,
  },
};

export function ReportStatusBar({
  status,
  generatedLabel,
}: {
  status: ReportStatus;
  generatedLabel?: string | undefined;
}) {
  const config = CONFIG[status];
  const Icon = config.icon;

  return (
    <Card className="border-border bg-card shadow-none">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${config.className}`}
          >
            <Icon className={`h-4 w-4 ${config.spin ? "animate-spin" : ""}`} aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-foreground">{config.label}</p>
            <p className="text-sm text-muted-foreground">{config.detail}</p>
          </div>
        </div>
        <Badge variant="outline" className="w-fit shrink-0 border-border text-muted-foreground">
          {status === "success" ? (generatedLabel ?? "Live analysis") : "Connected models"}
        </Badge>
      </CardContent>
    </Card>
  );
}
