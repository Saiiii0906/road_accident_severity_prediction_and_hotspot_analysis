import type { Control, FieldPath } from "react-hook-form";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { Option } from "@/constants/severity";
import type { SeverityFormValues } from "@/components/severity/severity-schema";

type Name = FieldPath<SeverityFormValues>;

interface BaseProps {
  control: Control<SeverityFormValues>;
  name: Name;
  label: string;
  helper?: string;
}

function RequiredMark() {
  return (
    <span className="text-danger" aria-hidden>
      *
    </span>
  );
}

export function SelectField({
  control,
  name,
  label,
  helper,
  options,
  placeholder = "Select…",
}: BaseProps & { options: Option[]; placeholder?: string }) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {label} <RequiredMark />
          </FormLabel>
          <Select
            onValueChange={field.onChange}
            value={typeof field.value === "string" ? field.value : ""}
          >
            <FormControl>
              <SelectTrigger className="bg-card">
                <SelectValue placeholder={placeholder} />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {helper ? <FormDescription>{helper}</FormDescription> : null}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function NumberField({
  control,
  name,
  label,
  helper,
  min = 0,
  max,
}: BaseProps & { min?: number; max?: number }) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {label} <RequiredMark />
          </FormLabel>
          <FormControl>
            <Input
              type="number"
              inputMode="numeric"
              min={min}
              {...(max !== undefined && { max })}
              className="bg-card"
              {...field}
              value={field.value ?? ""}
            />
          </FormControl>
          {helper ? <FormDescription>{helper}</FormDescription> : null}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function DateTimeField({
  control,
  name,
  label,
  helper,
  type,
}: BaseProps & { type: "date" | "time" }) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {label} <RequiredMark />
          </FormLabel>
          <FormControl>
            <Input
              type={type}
              className="bg-card"
              {...field}
              value={typeof field.value === "string" ? field.value : ""}
            />
          </FormControl>
          {helper ? <FormDescription>{helper}</FormDescription> : null}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function SegmentedField({
  control,
  name,
  label,
  helper,
  options,
}: BaseProps & { options: Option[] }) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {label} <RequiredMark />
          </FormLabel>
          <FormControl>
            <ToggleGroup
              type="single"
              variant="outline"
              value={typeof field.value === "string" ? field.value : ""}
              onValueChange={(value) => {
                if (value) field.onChange(value);
              }}
              className="w-full justify-start"
            >
              {options.map((option) => (
                <ToggleGroupItem
                  key={option.value}
                  value={option.value}
                  className="flex-1 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                >
                  {option.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </FormControl>
          {helper ? <FormDescription>{helper}</FormDescription> : null}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
