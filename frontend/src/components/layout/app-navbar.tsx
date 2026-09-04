import { Menu, Search } from "lucide-react";
import { Breadcrumbs } from "@/components/common/breadcrumbs";
import { ThemeToggle } from "@/components/common/theme-toggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NotificationPopover } from "@/components/notifications/notification-popover";

interface AppNavbarProps {
  onOpenMobileNav: () => void;
}

export function AppNavbar({ onOpenMobileNav }: AppNavbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-sm sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="shrink-0 lg:hidden"
        aria-label="Open navigation"
        onClick={onOpenMobileNav}
      >
        <Menu className="h-4 w-4" />
      </Button>

      <div className="min-w-0 flex-1">
        <Breadcrumbs />
      </div>

      <div className="relative hidden w-64 shrink-0 md:block">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          type="search"
          placeholder="Search segments, reports…"
          aria-label="Search"
          className="h-9 bg-card pl-9"
        />
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <NotificationPopover />
        <ThemeToggle />
        <button
          type="button"
          aria-label="Account"
          className="ml-1 flex shrink-0 items-center gap-2.5 rounded-lg border border-border bg-card px-2 py-1.5 text-left transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-primary text-[10px] font-bold text-primary-foreground">
            AV
          </span>
          <span className="hidden text-xs leading-tight sm:block">
            <span className="block font-bold">Analyst</span>
            <span className="block text-muted-foreground">Workspace</span>
          </span>
        </button>
      </div>
    </header>
  );
}
