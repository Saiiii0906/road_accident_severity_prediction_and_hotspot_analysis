import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { ArrowRight, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/common/theme-toggle";
import { WorkflowSection } from "@/components/landing/workflow-section";
import { FeatureSection } from "@/components/landing/feature-section";
import { ValueSection } from "@/components/landing/value-section";
import { SiteFooter } from "@/components/landing/site-footer";
import { APP_NAME } from "@/constants/navigation";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Vantage — AI Traffic Intelligence & Road Safety Platform" },
      {
        name: "description",
        content:
          "Predict accident severity, discover hotspots, assess road risk and generate AI infrastructure recommendations for safer transportation systems.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:title", content: "Vantage — AI Traffic Intelligence" },
      {
        property: "og:description",
        content:
          "Predict. Analyze. Improve road safety — AI-powered severity prediction, hotspot analysis and infrastructure reporting.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  const scrollToWorkflow = () => {
    document.getElementById("workflow")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur sm:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">
            <ShieldAlert className="h-4 w-4" aria-hidden />
          </span>
          <span className="truncate text-sm font-bold tracking-tight">{APP_NAME}</span>
        </div>
        <ThemeToggle />
        <Button asChild size="sm" variant="outline">
          <Link to="/dashboard">Open workspace</Link>
        </Button>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 sm:px-8">
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="py-24 lg:py-32"
          aria-labelledby="hero-title"
        >
          <p className="text-xs font-bold tracking-[0.2em] text-primary uppercase">
            AI-powered traffic intelligence
          </p>
          <h1
            id="hero-title"
            className="mt-6 max-w-4xl text-4xl leading-[1.05] text-foreground sm:text-6xl lg:text-7xl"
          >
            Predict. Analyze.
            <br />
            Improve Road Safety.
          </h1>
          <p className="mt-8 max-w-2xl text-base text-muted-foreground sm:text-lg">
            Use AI to predict accident severity, discover accident hotspots, assess road risks, and
            generate infrastructure recommendations for smarter and safer transportation systems.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Button asChild size="lg" className="transition-transform hover:-translate-y-0.5">
              <Link to="/dashboard">
                Get Started
                <ArrowRight className="ml-1 h-4 w-4" aria-hidden />
              </Link>
            </Button>
            <Button size="lg" variant="ghost" onClick={scrollToWorkflow}>
              Learn More
            </Button>
          </div>
        </motion.section>

        <WorkflowSection />
        <FeatureSection />
        <ValueSection />
      </main>

      <SiteFooter />
    </div>
  );
}
