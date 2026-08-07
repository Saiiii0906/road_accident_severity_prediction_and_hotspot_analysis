import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { SectionHeader } from "@/components/common/section-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { AI_INSIGHTS } from "@/constants/content";

const config = {
  critical: { icon: ShieldAlert, label: "Critical", className: "text-danger" },
  warning: { icon: AlertTriangle, label: "Warning", className: "text-warning" },
  info: { icon: Info, label: "Insight", className: "text-primary" },
};

export function InsightsPanel() {
  return (
    <Card className="h-full border-border bg-card shadow-none">
      <CardHeader className="border-b border-border">
        <SectionHeader
          title="AI insights"
          description="Signals detected across the current dataset."
        />
      </CardHeader>
      <CardContent className="p-5">
        <ul className="space-y-3">
          {AI_INSIGHTS.map((insight) => {
            const { icon: Icon, label, className } = config[insight.level];
            return (
              <li
                key={insight.text}
                className="flex items-start gap-3 rounded-xl border border-border bg-muted/20 p-4 transition-colors duration-300 hover:bg-muted/40"
              >
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${className}`} aria-hidden />
                <div className="min-w-0 space-y-2">
                  <p className="text-sm text-foreground">{insight.text}</p>
                  <Badge variant="outline" className="text-[10px] tracking-wide uppercase">
                    {label}
                  </Badge>
                </div>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
