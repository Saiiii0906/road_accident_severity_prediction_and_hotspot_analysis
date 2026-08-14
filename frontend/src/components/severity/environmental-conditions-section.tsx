import type { Control } from "react-hook-form";
import { SectionHeader } from "@/components/common/section-header";
import {
  AREA_TYPES,
  LIGHT_CONDITIONS,
  VISIBILITY_LEVELS,
  WEATHER_CONDITIONS,
} from "@/constants/severity";
import { SegmentedField, SelectField } from "@/components/severity/form-fields";
import type { SeverityFormValues } from "@/components/severity/severity-schema";

export function EnvironmentalConditionsSection({
  control,
}: {
  control: Control<SeverityFormValues>;
}) {
  return (
    <section className="space-y-5">
      <SectionHeader
        title="Environmental conditions"
        description="Weather, lighting and setting surrounding the incident."
      />
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <SelectField
          control={control}
          name="weather"
          label="Weather conditions"
          options={WEATHER_CONDITIONS}
        />
        <SelectField
          control={control}
          name="lightConditions"
          label="Light conditions"
          options={LIGHT_CONDITIONS}
        />
        <SelectField
          control={control}
          name="visibility"
          label="Visibility"
          options={VISIBILITY_LEVELS}
        />
        <div className="sm:col-span-2 xl:col-span-3">
          <SegmentedField
            control={control}
            name="areaType"
            label="Area context"
            options={AREA_TYPES}
            helper="Urban areas typically carry lower speeds but higher exposure."
          />
        </div>
      </div>
    </section>
  );
}
