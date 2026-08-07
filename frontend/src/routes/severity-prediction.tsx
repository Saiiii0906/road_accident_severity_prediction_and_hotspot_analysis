import { createFileRoute } from "@tanstack/react-router";
import { Gauge } from "lucide-react";
import { PlaceholderPage } from "@/components/common/placeholder-page";

export const Route = createFileRoute("/severity-prediction")({
  head: () => ({
    meta: [
      { title: "Severity Prediction — Vantage" },
      {
        name: "description",
        content:
          "Estimate expected accident severity from road, weather and collision context inputs.",
      },
      { property: "og:title", content: "Severity Prediction — Vantage" },
      {
        property: "og:description",
        content: "Estimate expected accident severity for a described collision scenario.",
      },
    ],
  }),
  component: () => (
    <PlaceholderPage
      eyebrow="Modelling"
      title="Severity prediction"
      description="Describe a collision scenario — road class, junction type, lighting, weather and time — to estimate the expected severity outcome."
      icon={Gauge}
      emptyTitle="Prediction interface not connected yet"
      emptyDescription="The scenario form and model output panel will appear here once the prediction service is wired up."
    />
  ),
});
