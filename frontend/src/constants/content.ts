import {
  BrainCircuit,
  Gauge,
  MapPinned,
  Route as RouteIcon,
  Navigation,
  ShieldCheck,
  Sparkles,
  Compass,
  History,
  type LucideIcon,
} from "lucide-react";

export const APP_VERSION = "v1.0.0";

export interface WorkflowStep {
  icon: LucideIcon;
  title: string;
  body: string;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    icon: Navigation,
    title: "Journey Parameters",
    body: "Enter origin, destination, and departure schedule for live corridor evaluation.",
  },
  {
    icon: Gauge,
    title: "Severity Prediction",
    body: "Estimate collision outcome severity across slight, serious, and fatal classes.",
  },
  {
    icon: MapPinned,
    title: "Hotspot Explorer",
    body: "Identify historical spatial clusters and priority safety zones.",
  },
  {
    icon: RouteIcon,
    title: "Road Risk Assessment",
    body: "Continuous risk profiling across road layouts and environmental conditions.",
  },
  {
    icon: BrainCircuit,
    title: "AI Decision Support",
    body: "Generate explainable infrastructure interventions and grounded route summaries.",
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
    icon: Navigation,
    title: "Journey Safety Analysis",
    body: "Multi-factor corridor safety evaluation combining live weather, traffic, incidents, and historical collisions.",
    to: "/dashboard",
  },
  {
    icon: Gauge,
    title: "Severity Prediction",
    body: "Predict accident severity using environmental, vehicle, and road characteristics.",
    to: "/severity-prediction",
  },
  {
    icon: MapPinned,
    title: "Hotspot Explorer",
    body: "Identify accident-prone areas using spatial clustering intelligence.",
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
  {
    icon: History,
    title: "Analysis History",
    body: "Comprehensive audit trail of prior predictions, corridor evaluations, and reports.",
    to: "/history",
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
