import { Filter, RotateCcw } from "lucide-react";
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
  RISK_PERIODS,
  RISK_REGIONS,
  RISK_ROAD_CONDITIONS,
  RISK_SEVERITIES,
  RISK_TIME_OF_DAY,
  RISK_WEATHER,
} from "@/constants/risk";
import type { RiskFilters as Filters } from "@/lib/api/risk";

interface RiskFiltersProps {
  value: Filters;
  isLoading: boolean;
  onChange: (next: Filters) => void;
  onApply: () => void;
  onReset: () => void;
}

function FilterSelect({
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

export function RiskFilters({ value, isLoading, onChange, onApply, onReset }: RiskFiltersProps) {
  const set =
    <K extends keyof Filters>(key: K) =>
    (next: Filters[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Analysis controls"
          description="Choose the network, period and conditions to analyse, then apply."
        />
      </CardHeader>
      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <FilterSelect
            id="risk-region"
            label="Region or area"
            options={RISK_REGIONS}
            value={value.region}
            onValueChange={set("region")}
          />
          <FilterSelect
            id="risk-period"
            label="Time period"
            options={RISK_PERIODS}
            value={value.period}
            onValueChange={set("period")}
          />
          <FilterSelect
            id="risk-severity"
            label="Risk level"
            options={RISK_SEVERITIES}
            value={value.severity}
            onValueChange={set("severity")}
          />
          <FilterSelect
            id="risk-road"
            label="Road condition"
            options={RISK_ROAD_CONDITIONS}
            value={value.roadCondition}
            onValueChange={set("roadCondition")}
          />
          <FilterSelect
            id="risk-weather"
            label="Weather condition"
            options={RISK_WEATHER}
            value={value.weather}
            onValueChange={set("weather")}
          />
          <FilterSelect
            id="risk-time"
            label="Time of day"
            options={RISK_TIME_OF_DAY}
            value={value.timeOfDay}
            onValueChange={set("timeOfDay")}
          />
        </div>

        <Separator />

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button className="flex-1" onClick={onApply} disabled={isLoading}>
            <Filter className="h-4 w-4" aria-hidden />
            {isLoading ? "Analysing…" : "Apply analysis"}
          </Button>
          <Button variant="outline" className="flex-1" onClick={onReset} disabled={isLoading}>
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
