import { z } from "zod";
import type { SeverityPredictionRequest } from "@/lib/api/severity";

const required = (message: string) => z.string().trim().min(1, { message });

export const severityFormSchema = z.object({
  date: required("Accident date is required"),
  time: required("Accident time is required"),
  dayOfWeek: required("Select the day of week"),
  vehicles: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .int({ message: "Use a whole number" })
    .min(1, { message: "At least 1 vehicle" })
    .max(50, { message: "Maximum 50 vehicles" }),
  casualties: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .int({ message: "Use a whole number" })
    .min(0, { message: "Cannot be negative" })
    .max(200, { message: "Maximum 200 casualties" }),
  speedLimit: required("Select a speed limit"),
  junctionControl: required("Select a junction or control type"),
  roadType: required("Select a road type"),
  trafficDensity: required("Select traffic density"),
  roadSurface: required("Select the road surface condition"),
  weather: required("Select weather conditions"),
  lightConditions: required("Select light conditions"),
  visibility: required("Select visibility"),
  areaType: required("Select urban or rural"),
  latitude: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .min(-90, { message: "Latitude must be between -90 and 90" })
    .max(90, { message: "Latitude must be between -90 and 90" }),
  longitude: z.coerce
    .number({ invalid_type_error: "Enter a number" })
    .min(-180, { message: "Longitude must be between -180 and 180" })
    .max(180, { message: "Longitude must be between -180 and 180" }),
});

export type SeverityFormValues = z.infer<typeof severityFormSchema>;

export const severityFormDefaults: Partial<SeverityFormValues> = {
  vehicles: 2,
  casualties: 1,
  areaType: "urban",
  trafficDensity: "moderate",
  visibility: "good",
  latitude: 0,
  longitude: 0,
};

export function toPredictionRequest(values: SeverityFormValues): SeverityPredictionRequest {
  return {
    accident_date: values.date,
    accident_time: values.time,
    day_of_week: values.dayOfWeek,
    number_of_vehicles: values.vehicles,
    number_of_casualties: values.casualties,
    speed_limit: Number(values.speedLimit),
    junction_control: values.junctionControl,
    road_type: values.roadType,
    traffic_density: values.trafficDensity,
    road_surface_conditions: values.roadSurface,
    weather_conditions: values.weather,
    light_conditions: values.lightConditions,
    urban_or_rural_area: values.areaType,
    latitude: values.latitude || 52.23759,
    longitude: values.longitude || -1.362233,
  };
}