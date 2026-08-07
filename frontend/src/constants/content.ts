import {
  BrainCircuit,
  ClipboardList,
  Gauge,
  MapPinned,
  Route as RouteIcon,
  ShieldCheck,
  Sparkles,
  Compass,
  FileDown,
  FileText,
  Activity,
  type LucideIcon,
} from "lucide-react";

export const APP_VERSION = "v0.2.0 — Sprint 2";

export interface WorkflowStep {
  icon: LucideIcon;
  title: string;
  body: string;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    icon: ClipboardList,
    title: "User Input",
    body: "Describe the collision context, road class and conditions.",
  },
  {
    icon: Gauge,
    title: "Severity Prediction",
    body: "Estimate expected outcome severity for the scenario.",
  },
  {
    icon: MapPinned,
    title: "Hotspot Analysis",
    body: "Locate spatial clusters of high-severity incidents.",
  },
  {
    icon: RouteIcon,
    title: "Road Risk Assessment",
    body: "Score corridors and junctions across risk indicators.",
  },
  {
    icon: BrainCircuit,
    title: "AI Infrastructure Report",
    body: "Produce explainable intervention recommendations.",
  },
];

export interface FeatureModule {
  icon: LucideIcon;
  title: string;
  body: string;
  to: string;
}

export const FEATURE_MODULES: FeatureModule[] = [
  {
    icon: Gauge,
    title: "Severity Prediction",
    body: "Predict accident severity using environmental, vehicle, and road characteristics.",
    to: "/severity-prediction",
  },
  {
    icon: MapPinned,
    title: "Hotspot Analysis",
    body: "Identify accident-prone areas using spatial intelligence.",
    to: "/hotspot-explorer",
  },
  {
    icon: RouteIcon,
    title: "Road Risk Analysis",
    body: "Evaluate road segments using multiple traffic and environmental indicators.",
    to: "/road-risk-analysis",
  },
  {
    icon: BrainCircuit,
    title: "AI Infrastructure Report",
    body: "Generate explainable recommendations for infrastructure improvements.",
    to: "/ai-infrastructure-report",
  },
];

export const VALUE_PILLARS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: Sparkles,
    title: "AI-Powered Analytics",
    body: "Model severity outcomes from historic collision patterns and surface the factors that drive them.",
  },
  {
    icon: Compass,
    title: "Spatial Intelligence",
    body: "Understand where risk concentrates across the network, from single junctions to whole corridors.",
  },
  {
    icon: ShieldCheck,
    title: "Decision Support",
    body: "Turn analysis into prioritised, reviewable interventions your team can defend and act on.",
  },
];

export interface Kpi {
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
}

export const DASHBOARD_KPIS: Kpi[] = [
  { label: "Accidents analyzed", value: "12,486", delta: "+12%", trend: "up" },
  { label: "High risk zones", value: "38", delta: "+4", trend: "up" },
  { label: "Average severity", value: "2.8", delta: "Stable", trend: "flat" },
  { label: "AI reports generated", value: "1,286", delta: "+18%", trend: "up" },
];

export const ANALYTICS_CARDS = [
  {
    title: "Severity distribution",
    description: "Outcome mix across analyzed incidents.",
    variant: "bars" as const,
  },
  {
    title: "Monthly trend",
    description: "Incident volume over the last 12 months.",
    variant: "line" as const,
  },
  {
    title: "Weather conditions",
    description: "Severity share by recorded weather.",
    variant: "donut" as const,
  },
  {
    title: "Road types",
    description: "Exposure split by road classification.",
    variant: "bars" as const,
  },
];

export interface Insight {
  text: string;
  level: "critical" | "warning" | "info";
}

export const AI_INSIGHTS: Insight[] = [
  {
    text: "High collision probability detected near urban intersections.",
    level: "critical",
  },
  {
    text: "Poor visibility contributes significantly during evening hours.",
    level: "warning",
  },
  { text: "Road maintenance is recommended for Segment A12.", level: "warning" },
  {
    text: "Rainfall increases severe accident probability by approximately 18%.",
    level: "info",
  },
];

export const RECENT_ACTIVITY: {
  icon: LucideIcon;
  title: string;
  meta: string;
}[] = [
  { icon: Gauge, title: "Severity Prediction completed", meta: "12 minutes ago" },
  { icon: MapPinned, title: "Hotspot Report generated", meta: "1 hour ago" },
  { icon: Activity, title: "Road Risk evaluated — Corridor N4", meta: "3 hours ago" },
  { icon: FileDown, title: "Infrastructure Report exported", meta: "Yesterday" },
  { icon: FileText, title: "Severity Prediction completed", meta: "Yesterday" },
];
