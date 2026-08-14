import { SectionHeader } from "@/components/common/section-header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { RECENT_ACTIVITY } from "@/constants/content";

export function ActivityList() {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader title="Recent activity" description="Latest runs in this workspace." />
      </CardHeader>
      <CardContent className="p-5">
        <ul className="divide-y divide-border">
          {RECENT_ACTIVITY.map((item, index) => (
            <li
              key={`${item.title}-${index}`}
              className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
            >
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-border bg-muted/40">
                <item.icon className="h-4 w-4 text-muted-foreground" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-foreground">{item.title}</p>
                <small className="text-muted-foreground">{item.meta}</small>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
