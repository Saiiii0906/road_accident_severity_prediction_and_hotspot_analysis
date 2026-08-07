import {
  LayoutDashboard,
  Gauge,
  MapPinned,
  Route as RouteIcon,
  BrainCircuit,
  History,
  type LucideIcon,
} from "lucide-react";

export const APP_NAME = "Vantage";
export const APP_TAGLINE = "Road Accident Severity Prediction & Hotspot Analysis";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  description: string;
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: LayoutDashboard,
    description: "Network-wide overview of severity signals and exposure.",
  },
  {
    label: "Severity Prediction",
    to: "/severity-prediction",
    icon: Gauge,
    description: "Estimate outcome severity for a described collision scenario.",
  },
  {
    label: "Hotspot Explorer",
    to: "/hotspot-explorer",
    icon: MapPinned,
    description: "Locate and compare spatial clusters of high-severity incidents.",
  },
  {
    label: "Road Risk Analysis",
    to: "/road-risk-analysis",
    icon: RouteIcon,
    description: "Segment-level risk profiling across corridors and junctions.",
  },
  {
    label: "AI Infrastructure Report",
    to: "/ai-infrastructure-report",
    icon: BrainCircuit,
    description: "Generated recommendations for infrastructure interventions.",
  },
  {
    label: "History",
    to: "/history",
    icon: History,
    description: "Every prediction, report and export produced in this workspace.",
  },
];
