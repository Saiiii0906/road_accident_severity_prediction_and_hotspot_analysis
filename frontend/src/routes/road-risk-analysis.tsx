import { createFileRoute } from "@tanstack/react-router";
import { Route as RouteIcon } from "lucide-react";
import { PlaceholderPage } from "@/components/common/placeholder-page";

export const Route = createFileRoute("/road-risk-analysis")({
  head: () => ({
    meta: [
      { title: "Road Risk Analysis — Vantage" },
      {
        name: "description",
        content:
          "Segment-level risk profiling across corridors, junctions and intersections.",
      },
      { property: "og:title", content: "Road Risk Analysis — Vantage" },
      {
        property: "og:description",
        content: "Segment-level risk profiling across corridors and junctions.",
      },
    ],
  }),
  component: () => (
    <PlaceholderPage
      eyebrow="Network profiling"
      title="Road risk analysis"
      description="Compare corridors and junctions by modelled risk contribution, exposure and structural characteristics."
      icon={RouteIcon}
      emptyTitle="Segment table not connected yet"
      emptyDescription="Ranked segment scoring and comparison views will render here once network data is available."
    />
  ),
});
