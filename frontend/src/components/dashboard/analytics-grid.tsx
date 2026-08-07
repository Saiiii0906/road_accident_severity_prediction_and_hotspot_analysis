import { motion } from "motion/react";
import { SectionHeader } from "@/components/common/section-header";
import { ChartPlaceholder } from "@/components/common/chart-placeholder";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ANALYTICS_CARDS } from "@/constants/content";

export function AnalyticsGrid() {
  return (
    <section className="grid gap-4 lg:grid-cols-2" aria-label="Analytics">
      {ANALYTICS_CARDS.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: index * 0.05, ease: "easeOut" }}
        >
          <Card className="group h-full border-border bg-card shadow-none transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card">
            <CardHeader className="border-b border-border">
              <SectionHeader title={card.title} description={card.description} />
            </CardHeader>
            <CardContent className="p-5">
              <ChartPlaceholder variant={card.variant} height={200} />
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </section>
  );
}
