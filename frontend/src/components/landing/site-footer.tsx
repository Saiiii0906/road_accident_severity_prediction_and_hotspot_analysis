import { APP_NAME } from "@/constants/navigation";
import { APP_VERSION } from "@/constants/content";

export function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto grid w-full max-w-screen-2xl gap-6 px-4 py-8 sm:px-6 sm:py-10 md:grid-cols-[minmax(0,1fr)_auto] md:items-center md:px-8 lg:px-12 xl:px-16">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg overflow-hidden border border-border/40 bg-card">
            <img src="/logo.png" alt="Vantage Logo" className="h-7 w-7 object-contain" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight text-foreground">{APP_NAME}</p>
            <small className="text-muted-foreground">
              Traffic intelligence & road safety platform — {APP_VERSION}
            </small>
          </div>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap items-center gap-5">
          <a
            href="https://github.com/Saiiii0906/road_accident_severity_prediction_and_hotspot_analysis"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            GitHub
          </a>
          <a
            href="https://github.com/Saiiii0906/road_accident_severity_prediction_and_hotspot_analysis#readme"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            Documentation
          </a>
          <a
            href="/#workflow"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            How it works
          </a>
        </nav>
      </div>
    </footer>
  );
}
