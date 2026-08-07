import { createFileRoute } from "@tanstack/react-router";
import { Download, FileText } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { SectionHeader } from "@/components/common/section-header";
import { EmptyState } from "@/components/common/empty-state";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { MapHero } from "@/components/dashboard/map-hero";
import { AnalyticsGrid } from "@/components/dashboard/analytics-grid";
import { InsightsPanel } from "@/components/dashboard/insights-panel";
import { ActivityList } from "@/components/dashboard/activity-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Vantage Road Safety Intelligence" },
      {
        name: "description",
        content:
          "Today's overview of accident severity signals, hotspot density, analytics and AI insights across the road network.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Dashboard — Vantage" },
      {
        property: "og:description",
        content: "Network overview of severity signals, hotspots, analytics and AI insights.",
      },
    ],
  }),
  component: Dashboard,
});

function formatToday() {
  return new Date().toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function Dashboard() {
  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow={`Today's overview · ${formatToday()}`}
          title="Welcome back"
          description="A consolidated view of severity outcomes, hotspot density, corridor exposure and AI-detected signals across the monitored road network."
          actions={
            <>
              <Button variant="outline" size="sm">
                <Download className="mr-1.5 h-4 w-4" aria-hidden />
                Export
              </Button>
              <Button size="sm">New prediction</Button>
            </>
          }
        />

        <KpiGrid />

        <section aria-label="Hotspot map">
          <MapHero />
        </section>

        <AnalyticsGrid />

        <section className="grid gap-4 lg:grid-cols-2" aria-label="Insights and activity">
          <InsightsPanel />
          <ActivityList />
        </section>

        <section aria-label="Saved reports">
          <Card className="border-border bg-card shadow-none">
            <CardHeader className="border-b border-border">
              <SectionHeader
                title="Saved reports"
                description="Reports you pin for review appear here."
              />
            </CardHeader>
            <CardContent className="p-5">
              <EmptyState
                icon={FileText}
                title="No saved reports yet"
                description="Generate an AI infrastructure report and pin it to keep the assessments your team is reviewing within reach."
                action={<Button size="sm">Generate report</Button>}
              />
            </CardContent>
          </Card>
        </section>
      </div>
    </AppShell>
  );
}
