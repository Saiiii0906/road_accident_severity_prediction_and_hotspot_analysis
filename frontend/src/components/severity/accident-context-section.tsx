import type { Control } from "react-hook-form";
import { SectionHeader } from "@/components/common/section-header";
import { DAYS_OF_WEEK } from "@/constants/severity";
import { DateTimeField, NumberField, SelectField } from "@/components/severity/form-fields";
import type { SeverityFormValues } from "@/components/severity/severity-schema";

export function AccidentContextSection({ control }: { control: Control<SeverityFormValues> }) {
  return (
    <section className="space-y-5">
      <SectionHeader
        title="Accident context"
        description="When the incident occurred and how many road users were involved."
      />
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <DateTimeField control={control} name="date" label="Accident date" type="date" />
        <DateTimeField control={control} name="time" label="Accident time" type="time" />
        <SelectField
          control={control}
          name="dayOfWeek"
          label="Day of week"
          options={DAYS_OF_WEEK}
        />
        <NumberField control={control} name="vehicles" label="Vehicles involved" min={1} max={50} />
        <NumberField
          control={control}
          name="casualties"
          label="Casualties"
          min={0}
          max={200}
          helper="People injured or killed, excluding uninjured occupants."
        />
      </div>
    </section>
  );
}
