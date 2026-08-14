import { motion } from "motion/react";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FEATURE_MODULES } from "@/constants/content";

export function FeatureSection() {
  return (
    <section aria-labelledby="modules-title" className="py-20">
      <div className="max-w-2xl">
        <p className="text-xs font-bold tracking-[0.2em] text-primary uppercase">Modules</p>
        <h2 id="modules-title" className="mt-4 text-3xl text-foreground sm:text-4xl">
          Four analysis modules, one workspace
        </h2>
      </div>

      <div className="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {FEATURE_MODULES.map((module, index) => (
          <motion.div
            key={module.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.07, ease: "easeOut" }}
          >
            <Card className="h-full border-border bg-card shadow-none transition-all duration-300 hover:-translate-y-1 hover:shadow-card">
              <CardContent className="flex h-full flex-col gap-3 p-6">
                <span className="grid h-10 w-10 place-items-center rounded-lg border border-border bg-muted/50">
                  <module.icon className="h-4 w-4 text-primary" aria-hidden />
                </span>
                <h3 className="text-base text-foreground">{module.title}</h3>
                <p className="flex-1 text-sm text-muted-foreground">{module.body}</p>
                <Button asChild variant="outline" size="sm" className="mt-2 self-start">
                  <Link to={module.to}>
                    Open module
                    <ArrowUpRight className="ml-1 h-3.5 w-3.5" aria-hidden />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
