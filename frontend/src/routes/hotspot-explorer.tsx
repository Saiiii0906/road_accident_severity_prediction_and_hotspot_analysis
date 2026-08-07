import { createFileRoute } from "@tanstack/react-router";
import { MapPinned } from "lucide-react";
import { PlaceholderPage } from "@/components/common/placeholder-page";

export const Route = createFileRoute("/hotspot-explorer")({
  head: () => ({
    meta: [
      { title: "Hotspot Explorer — Vantage" },
      {
        name: "description",
        content:
          "Locate, filter and compare spatial clusters of high-severity road incidents.",
      },
      { property: "og:title", content: "Hotspot Explorer — Vantage" },
      {
        property: "og:description",
        content: "Locate and compare spatial clusters of high-severity road incidents.",
      },
    ],
  }),
  component: () => (
    <PlaceholderPage
      eyebrow="Spatial analysis"
      title="Hotspot explorer"
      description="Filter incident clusters by severity, period and road class to understand where risk persistently concentrates."
      icon={MapPinned}
      emptyTitle="Map surface reserved"
      emptyDescription="The interactive map, cluster list and filter rail will be implemented in a later sprint."
    />
  ),
});
