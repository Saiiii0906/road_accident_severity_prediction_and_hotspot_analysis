import { useState, type ReactNode } from "react";
import { motion } from "motion/react";
import { AppNavbar } from "@/components/layout/app-navbar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
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
        <footer className="border-t border-border px-4 py-5 sm:px-6 lg:px-10">
          <small className="text-muted-foreground">
            Frontend foundation — data services connect in a later sprint.
          </small>
        </footer>
      </div>
    </div>
  );
}
