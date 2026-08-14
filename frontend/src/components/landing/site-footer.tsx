import { ShieldAlert } from "lucide-react";
import { APP_NAME } from "@/constants/navigation";
import { APP_VERSION } from "@/constants/content";

export function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-10 sm:px-8 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">
            <ShieldAlert className="h-4 w-4" aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight text-foreground">{APP_NAME}</p>
            <small className="text-muted-foreground">
              Traffic intelligence platform — {APP_VERSION}
            </small>
          </div>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap items-center gap-5">
          <a
            href="#"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            GitHub
          </a>
          <a
            href="#"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            Documentation
          </a>
          <a
            href="#workflow"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            How it works
          </a>
        </nav>
      </div>
    </footer>
  );
}
