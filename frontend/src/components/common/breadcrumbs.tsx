import { Link, useRouterState } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { NAV_ITEMS, APP_NAME } from "@/constants/navigation";

export function Breadcrumbs() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const current = NAV_ITEMS.find((item) => item.to === pathname);

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      <ol className="flex min-w-0 items-center gap-1.5 text-sm">
        <li className="shrink-0">
          <Link
            to="/"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            {APP_NAME}
          </Link>
        </li>
        <li aria-hidden className="shrink-0">
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
        </li>
        <li className="min-w-0 truncate font-bold text-foreground" aria-current="page">
          {current?.label ?? "Workspace"}
        </li>
      </ol>
    </nav>
  );
}
