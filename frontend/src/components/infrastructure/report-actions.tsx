import { FileSearch, RefreshCw, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ReportActions({
  isGenerating,
  canExport = true,
  isExporting = false,
  onGenerate,
  onRefresh,
  onExport,
}: {
  isGenerating: boolean;
  canExport?: boolean;
  isExporting?: boolean;
  onGenerate: () => void;
  onRefresh: () => void;
  onExport: () => void;
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="min-w-0 text-sm text-muted-foreground">
          Generate and review an evidence-grounded infrastructure report from the connected analysis
          pipeline.
        </p>
        <div className="flex flex-wrap gap-2 sm:shrink-0">
          <Button size="sm" onClick={onGenerate} disabled={isGenerating}>
            <FileSearch className="h-4 w-4" aria-hidden />
            Generate report
          </Button>
          <Button size="sm" variant="outline" onClick={onRefresh} disabled={isGenerating}>
            <RefreshCw className="h-4 w-4" aria-hidden />
            Refresh analysis
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onExport}
            disabled={!canExport || isGenerating || isExporting}
          >
            <Download className="h-4 w-4" aria-hidden />
            {isExporting ? "Exporting…" : "Export PDF report"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
