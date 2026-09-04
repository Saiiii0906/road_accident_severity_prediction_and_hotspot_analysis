import type { Control } from "react-hook-form";
import { SectionHeader } from "@/components/common/section-header";
import { JUNCTION_CONTROLS, ROAD_SURFACES, ROAD_TYPES, SPEED_LIMITS } from "@/constants/severity";
import { SelectField } from "@/components/severity/form-fields";
import type { SeverityFormValues } from "@/components/severity/severity-schema";

export function RoadConditionsSection({ control }: { control: Control<SeverityFormValues> }) {
  return (
    <section className="space-y-5">
      <SectionHeader
        title="Road & traffic conditions"
        description="Physical road characteristics and highway geometry at the incident location."
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          control={control}
          name="speedLimit"
          label="Speed limit"
          options={SPEED_LIMITS}
        />
        <SelectField
          control={control}
          name="junctionControl"
          label="Junction / control type"
          options={JUNCTION_CONTROLS}
        />
        <SelectField control={control} name="roadType" label="Road type" options={ROAD_TYPES} />
        <SelectField
          control={control}
          name="roadSurface"
          label="Road surface condition"
          options={ROAD_SURFACES}
        />
      </div>
    </section>
  );
}
