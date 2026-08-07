import { createFileRoute } from "@tanstack/react-router";
import { BrainCircuit } from "lucide-react";
import { PlaceholderPage } from "@/components/common/placeholder-page";

export const Route = createFileRoute("/ai-infrastructure-report")({
  head: () => ({
    meta: [
      { title: "AI Infrastructure Report — Vantage" },
      {
        name: "description",
        content:
          "Generated, reviewable infrastructure intervention recommendations from road risk signals.",
      },
      { property: "og:title", content: "AI Infrastructure Report — Vantage" },
      {
        property: "og:description",
        content: "Reviewable infrastructure intervention recommendations from risk signals.",
      },
    ],
  }),
  component: () => (
    <PlaceholderPage
      eyebrow="Advisory"
      title="AI infrastructure report"
      description="Turn severity and hotspot findings into a structured, prioritised set of infrastructure recommendations ready for engineering review."
      icon={BrainCircuit}
      emptyTitle="Report generation not enabled yet"
      emptyDescription="Report composition, review states and export options will be added in a later sprint."
    />
  ),
});
