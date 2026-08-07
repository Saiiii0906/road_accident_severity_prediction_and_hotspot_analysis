import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/common/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/common/empty-state";
import type { LucideIcon } from "lucide-react";

interface PlaceholderPageProps {
  eyebrow: string;
  title: string;
  description: string;
  icon: LucideIcon;
  emptyTitle: string;
  emptyDescription: string;
}

export function PlaceholderPage({
  eyebrow,
  title,
  description,
  icon,
  emptyTitle,
  emptyDescription,
}: PlaceholderPageProps) {
  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader eyebrow={eyebrow} title={title} description={description} />
        <Card className="border-border bg-card shadow-none transition-shadow hover:shadow-card">
          <CardContent className="p-0">
            <EmptyState icon={icon} title={emptyTitle} description={emptyDescription} />
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
