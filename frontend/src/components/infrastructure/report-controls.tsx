import { FileSearch, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SectionHeader } from "@/components/common/section-header";
import type { Option } from "@/constants/severity";
import {
  REPORT_FOCUS_OPTIONS,
  REPORT_PERIODS,
  REPORT_REGIONS,
  REPORT_THRESHOLDS,
} from "@/constants/infrastructure";
import type { ReportFilters } from "@/lib/api/infrastructure";

interface ReportControlsProps {
  value: ReportFilters;
  isGenerating: boolean;
  onChange: (next: ReportFilters) => void;
  onGenerate: () => void;
  onReset: () => void;
}

function ControlSelect({
  id,
  label,
  options,
  value,
  onValueChange,
}: {
  id: string;
  label: string;
  options: Option[];
  value: string;
  onValueChange: (next: string) => void;
}) {
  return (
    <div className="min-w-0 space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger id={id} className="w-full bg-card">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function ReportControls({
  value,
  isGenerating,
  onChange,
  onGenerate,
  onReset,
}: ReportControlsProps) {
  const set =
    <K extends keyof ReportFilters>(key: K) =>
    (next: ReportFilters[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Report controls"
          description="Set the scope and focus, then generate the interface report."
        />
      </CardHeader>
      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <ControlSelect
            id="report-region"
            label="Region or area"
            options={REPORT_REGIONS}
            value={value.region}
            onValueChange={set("region")}
          />
          <ControlSelect
            id="report-period"
            label="Analysis period"
            options={REPORT_PERIODS}
            value={value.period}
            onValueChange={set("period")}
          />
          <ControlSelect
            id="report-threshold"
            label="Risk threshold"
            options={REPORT_THRESHOLDS}
            value={value.threshold}
            onValueChange={set("threshold")}
          />
          <ControlSelect
            id="report-focus"
            label="Report focus"
            options={REPORT_FOCUS_OPTIONS}
            value={value.focus}
            onValueChange={set("focus")}
          />
        </div>

        <Separator />

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button className="flex-1" onClick={onGenerate} disabled={isGenerating}>
            <FileSearch className="h-4 w-4" aria-hidden />
            {isGenerating ? "Generating…" : "Generate report"}
          </Button>
          <Button variant="outline" className="flex-1" onClick={onReset} disabled={isGenerating}>
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
