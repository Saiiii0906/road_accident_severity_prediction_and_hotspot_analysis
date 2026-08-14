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
  HOTSPOT_DENSITIES,
  HOTSPOT_PERIODS,
  HOTSPOT_REGIONS,
  HOTSPOT_ROAD_CONDITIONS,
  HOTSPOT_SEVERITIES,
  HOTSPOT_WEATHER,
} from "@/constants/hotspots";
import type { HotspotFilters as Filters } from "@/lib/api/hotspots";

interface HotspotFiltersProps {
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

export function HotspotFilters({
  value,
  isLoading,
  onChange,
  onApply,
  onReset,
}: HotspotFiltersProps) {
  const set =
    <K extends keyof Filters>(key: K) =>
    (next: Filters[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="Filters"
          description="Narrow the analysis to the network, period and conditions you are reviewing."
        />
      </CardHeader>
      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <FilterSelect
            id="hotspot-region"
            label="Region or area"
            options={HOTSPOT_REGIONS}
            value={value.region}
            onValueChange={set("region")}
          />
          <FilterSelect
            id="hotspot-severity"
            label="Severity level"
            options={HOTSPOT_SEVERITIES}
            value={value.severity}
            onValueChange={set("severity")}
          />
          <FilterSelect
            id="hotspot-period"
            label="Time period"
            options={HOTSPOT_PERIODS}
            value={value.period}
            onValueChange={set("period")}
          />
          <FilterSelect
            id="hotspot-density"
            label="Accident density"
            options={HOTSPOT_DENSITIES}
            value={value.density}
            onValueChange={set("density")}
          />
          <FilterSelect
            id="hotspot-weather"
            label="Weather condition"
            options={HOTSPOT_WEATHER}
            value={value.weather}
            onValueChange={set("weather")}
          />
          <FilterSelect
            id="hotspot-road"
            label="Road condition"
            options={HOTSPOT_ROAD_CONDITIONS}
            value={value.roadCondition}
            onValueChange={set("roadCondition")}
          />
        </div>

        <Separator />

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button className="flex-1" onClick={onApply} disabled={isLoading}>
            <Filter className="h-4 w-4" aria-hidden />
            {isLoading ? "Applying…" : "Apply filters"}
          </Button>
          <Button variant="outline" className="flex-1" onClick={onReset} disabled={isLoading}>
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset filters
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
