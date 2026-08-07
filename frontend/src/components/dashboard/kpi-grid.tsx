import { motion } from "motion/react";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DASHBOARD_KPIS } from "@/constants/content";

const trendIcon = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

const trendColor = {
  up: "text-success",
  down: "text-danger",
  flat: "text-muted-foreground",
};

export function KpiGrid() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Key metrics">
      {DASHBOARD_KPIS.map((kpi, index) => {
        const Icon = trendIcon[kpi.trend];
        return (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: index * 0.06, ease: "easeOut" }}
          >
            <Card className="border-border bg-card shadow-none transition-all duration-300 hover:-translate-y-1 hover:shadow-card">
              <CardContent className="space-y-3 p-5">
                <p className="text-xs font-bold tracking-wide text-muted-foreground uppercase">
                  {kpi.label}
                </p>
                <p className="text-3xl leading-none font-bold text-foreground">
                  {kpi.value}
                </p>
                <p
                  className={`flex items-center gap-1.5 text-xs ${trendColor[kpi.trend]}`}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden />
                  {kpi.delta}
                  <span className="text-muted-foreground">vs last month</span>
                </p>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </section>
  );
}
