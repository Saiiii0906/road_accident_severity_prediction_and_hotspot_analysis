import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
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
      <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto grid h-16 w-full max-w-screen-2xl grid-cols-2 items-center px-4 sm:grid-cols-3 sm:px-6 md:px-8 lg:px-12 xl:px-16">
          {/* 1. Left of the website */}
          <div className="flex items-center justify-start">
            <Link to="/" className="flex min-w-0 items-center gap-2.5">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg overflow-hidden border border-border/40 bg-card">
                <img src="/logo.png" alt="Vantage Logo" className="h-7 w-7 object-contain" />
              </span>
              <span className="truncate text-sm font-bold tracking-tight">{APP_NAME}</span>
            </Link>
          </div>

          {/* 2. Center of the website */}
          <nav
            className="hidden items-center justify-center gap-8 sm:flex"
            aria-label="Main Navigation"
          >
            <button
              type="button"
              onClick={scrollToWorkflow}
              className="cursor-pointer text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() =>
                document.getElementById("modules")?.scrollIntoView({ behavior: "smooth" })
              }
              className="cursor-pointer text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Modules
            </button>
            <button
              type="button"
              onClick={() =>
                document.getElementById("capabilities")?.scrollIntoView({ behavior: "smooth" })
              }
              className="cursor-pointer text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Capabilities
            </button>
          </nav>

          {/* 3. Right of the website */}
          <div className="flex items-center justify-end">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-screen-2xl px-4 sm:px-6 md:px-8 lg:px-12 xl:px-16">
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="py-12 sm:py-16 lg:py-20"
          aria-labelledby="hero-title"
        >
          <div className="grid gap-8 lg:grid-cols-12 lg:items-start lg:gap-12 xl:gap-16">
            <div className="lg:col-span-7 xl:col-span-8">
              <p className="text-xs font-bold tracking-[0.2em] text-primary uppercase">
                AI-powered traffic intelligence
              </p>
              <h1
                id="hero-title"
                className="mt-4 text-4xl font-extrabold leading-[1.08] tracking-tight text-foreground sm:text-6xl lg:text-6xl xl:text-7xl"
              >
                Predict. Analyze.
                <br />
                Improve Road Safety.
              </h1>
            </div>

            <div className="lg:col-span-5 xl:col-span-4 lg:pt-8">
              <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                Use AI to predict accident severity, discover accident hotspots, assess road risks,
                and generate infrastructure recommendations for smarter and safer transportation
                systems.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Button asChild size="lg" className="transition-transform hover:-translate-y-0.5">
                  <Link to="/dashboard">
                    Launch Workspace
                    <ArrowRight className="ml-1 h-4 w-4" aria-hidden />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" onClick={scrollToWorkflow}>
                  How It Works
                </Button>
              </div>
            </div>
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
