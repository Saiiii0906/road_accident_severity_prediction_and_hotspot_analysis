import { Filter, RotateCcw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
  HISTORY_PERIODS,
  HISTORY_REGIONS,
  HISTORY_STATUSES,
  HISTORY_TYPES,
} from "@/constants/history";
import type { HistoryFilters as Filters } from "@/lib/api/history";

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

export function HistoryFiltersPanel({
  value,
  isLoading,
  onChange,
  onApply,
  onReset,
}: {
  value: Filters;
  isLoading: boolean;
  onChange: (next: Filters) => void;
  onApply: () => void;
  onReset: () => void;
}) {
  const set =
    <K extends keyof Filters>(key: K) =>
    (next: Filters[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <Card className="border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="History controls"
          description="Narrow the record set by analysis type, area, period or status."
        />
      </CardHeader>
      <CardContent className="space-y-5 p-5 sm:p-6">
        <form
          className="min-w-0 space-y-2"
          onSubmit={(event) => {
            event.preventDefault();
            onApply();
          }}
        >
          <Label htmlFor="history-search">Search</Label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              id="history-search"
              value={value.search}
              placeholder="Analysis name, area or result"
              className="bg-card pl-9"
              onChange={(event) => set("search")(event.target.value)}
            />
          </div>
        </form>

        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <FilterSelect
            id="history-type"
            label="Analysis type"
            options={HISTORY_TYPES}
            value={value.type}
            onValueChange={(next) => set("type")(next as Filters["type"])}
          />
          <FilterSelect
            id="history-region"
            label="Region or area"
            options={HISTORY_REGIONS}
            value={value.region}
            onValueChange={set("region")}
          />
          <FilterSelect
            id="history-period"
            label="Time period"
            options={HISTORY_PERIODS}
            value={value.period}
            onValueChange={set("period")}
          />
          <FilterSelect
            id="history-status"
            label="Status"
            options={HISTORY_STATUSES}
            value={value.status}
            onValueChange={(next) => set("status")(next as Filters["status"])}
          />
        </div>

        <Separator />

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button className="flex-1" onClick={onApply} disabled={isLoading}>
            <Filter className="h-4 w-4" aria-hidden />
            {isLoading ? "Filtering…" : "Filter"}
          </Button>
          <Button variant="outline" onClick={onReset} disabled={isLoading}>
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
