import { useState, type ReactNode } from "react";
import { motion } from "motion/react";
import { AppNavbar } from "@/components/layout/app-navbar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { APP_NAME } from "@/constants/navigation";
import { APP_VERSION } from "@/constants/content";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <aside
        className={cn(
          "sticky top-0 hidden h-screen shrink-0 border-r border-sidebar-border transition-[width] duration-300 ease-out lg:block",
          collapsed ? "w-16" : "w-64",
        )}
      >
        <AppSidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-72 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <AppSidebar onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <AppNavbar onOpenMobileNav={() => setMobileOpen(true)} />
        <motion.main
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-8 sm:px-6 lg:px-10 lg:py-10"
        >
          {children}
        </motion.main>
        <footer className="border-t border-border px-4 py-4 sm:px-6 lg:px-10">
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-muted-foreground">
            <span>
              {APP_NAME} &copy; {new Date().getFullYear()} — AI Traffic Intelligence & Road Safety
              Platform
            </span>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/Saiiii0906/road_accident_severity_prediction_and_hotspot_analysis"
                target="_blank"
                rel="noreferrer"
                className="transition-colors hover:text-foreground"
              >
                GitHub
              </a>
              <a
                href="https://github.com/Saiiii0906/road_accident_severity_prediction_and_hotspot_analysis#readme"
                target="_blank"
                rel="noreferrer"
                className="transition-colors hover:text-foreground"
              >
                Documentation
              </a>
              <a href="/#workflow" className="transition-colors hover:text-foreground">
                How it works
              </a>
              <span className="font-mono">{APP_VERSION}</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
