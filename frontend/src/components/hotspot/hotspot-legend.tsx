import { cn } from "@/lib/utils";
import { HOTSPOT_INTENSITY_DISPLAY, HOTSPOT_INTENSITY_ORDER } from "@/constants/hotspots";

export function HotspotLegend({ className }: { className?: string }) {
  return (
    <div className={cn("flex flex-wrap items-center gap-x-4 gap-y-2", className)}>
      <span className="text-xs font-bold tracking-[0.14em] text-muted-foreground uppercase">
        Intensity
      </span>
      {HOTSPOT_INTENSITY_ORDER.map((level) => {
        const display = HOTSPOT_INTENSITY_DISPLAY[level];
        return (
          <span key={level} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span
              className={cn(
                "h-2.5 w-2.5 rounded-full",
                display.dotClassName,
                level === "moderate" && "opacity-90",
                level === "low" && "opacity-80",
              )}
              aria-hidden
            />
            {display.label}
          </span>
        );
      })}
    </div>
  );
}
