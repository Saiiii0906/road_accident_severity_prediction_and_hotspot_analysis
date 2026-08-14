import type { SeverityLevel } from "@/lib/api/severity";

export interface Option {
  value: string;
  label: string;
}

export const DAYS_OF_WEEK: Option[] = [
  { value: "monday", label: "Monday" },
  { value: "tuesday", label: "Tuesday" },
  { value: "wednesday", label: "Wednesday" },
  { value: "thursday", label: "Thursday" },
  { value: "friday", label: "Friday" },
  { value: "saturday", label: "Saturday" },
  { value: "sunday", label: "Sunday" },
];

export const JUNCTION_CONTROLS: Option[] = [
  { value: "no_junction", label: "Not at a junction" },
  { value: "give_way", label: "Give way or uncontrolled" },
  { value: "stop_sign", label: "Stop sign" },
  { value: "traffic_signal", label: "Traffic signals" },
  { value: "roundabout", label: "Roundabout" },
  { value: "authorised_person", label: "Controlled by authorised person" },
];

export const ROAD_TYPES: Option[] = [
  { value: "single_carriageway", label: "Single carriageway" },
  { value: "dual_carriageway", label: "Dual carriageway" },
  { value: "one_way_street", label: "One-way street" },
  { value: "slip_road", label: "Slip road" },
  { value: "roundabout", label: "Roundabout" },
  { value: "motorway", label: "Motorway / expressway" },
];

export const TRAFFIC_DENSITY: Option[] = [
  { value: "light", label: "Light" },
  { value: "moderate", label: "Moderate" },
  { value: "heavy", label: "Heavy" },
  { value: "congested", label: "Congested" },
];

export const ROAD_SURFACES: Option[] = [
  { value: "dry", label: "Dry" },
  { value: "wet", label: "Wet or damp" },
  { value: "snow", label: "Snow" },
  { value: "ice", label: "Frost or ice" },
  { value: "flood", label: "Flooded" },
];

export const WEATHER_CONDITIONS: Option[] = [
  { value: "clear", label: "Clear" },
  { value: "raining", label: "Raining" },
  { value: "snowing", label: "Snowing" },
  { value: "fog", label: "Fog or mist" },
  { value: "high_winds", label: "High winds" },
];

export const LIGHT_CONDITIONS: Option[] = [
  { value: "daylight", label: "Daylight" },
  { value: "dusk", label: "Dusk or dawn" },
  { value: "dark_lit", label: "Dark — street lights on" },
  { value: "dark_unlit", label: "Dark — no street lighting" },
];

export const VISIBILITY_LEVELS: Option[] = [
  { value: "good", label: "Good — over 200 m" },
  { value: "moderate", label: "Moderate — 50 to 200 m" },
  { value: "poor", label: "Poor — under 50 m" },
];

export const AREA_TYPES: Option[] = [
  { value: "urban", label: "Urban" },
  { value: "rural", label: "Rural" },
];

export const SPEED_LIMITS: Option[] = [20, 30, 40, 50, 60, 70, 80, 100, 120].map((kph) => ({
  value: String(kph),
  label: `${kph} km/h`,
}));

export const SEVERITY_DISPLAY: Record<
  SeverityLevel,
  { label: string; description: string; className: string; barClassName: string }
> = {
  low: {
    label: "Low",
    description: "Minor outcome expected — slight or no injury.",
    className: "border-success/30 bg-success/10 text-success",
    barClassName: "bg-success",
  },
  moderate: {
    label: "Moderate",
    description: "Injury likely but not life-threatening.",
    className: "border-warning/30 bg-warning/10 text-warning",
    barClassName: "bg-warning",
  },
  high: {
    label: "High",
    description: "Serious injury outcome expected.",
    className: "border-danger/30 bg-danger/10 text-danger",
    barClassName: "bg-danger",
  },
  fatal: {
    label: "Fatal",
    description: "Fatal outcome indicated for this scenario.",
    className: "border-danger/40 bg-danger/15 text-danger",
    barClassName: "bg-danger",
  },
};
