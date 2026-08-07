import { createFileRoute } from "@tanstack/react-router";
import { History } from "lucide-react";
import { PlaceholderPage } from "@/components/common/placeholder-page";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History — Vantage" },
      {
        name: "description",
        content:
          "Audit trail of every severity prediction, hotspot query and generated report in the workspace.",
      },
      { property: "og:title", content: "History — Vantage" },
      {
        property: "og:description",
        content: "Audit trail of predictions, hotspot queries and generated reports.",
      },
    ],
  }),
  component: () => (
    <PlaceholderPage
      eyebrow="Workspace"
      title="History"
      description="A chronological record of predictions, hotspot queries and reports, with the inputs used for each run."
      icon={History}
      emptyTitle="No activity recorded yet"
      emptyDescription="Once services are connected, every run in this workspace will be listed here with its parameters."
    />
  ),
});
