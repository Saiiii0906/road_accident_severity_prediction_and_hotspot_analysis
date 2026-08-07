import { cn } from "@/lib/utils";

type Variant = "bars" | "line" | "donut";

const BAR_HEIGHTS = [42, 68, 54, 88, 62, 76, 48];

export function ChartPlaceholder({
  variant = "bars",
  height = 200,
  className,
}: {
  variant?: Variant;
  height?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-dashed border-border bg-muted/25 p-4",
        className,
      )}
      style={{ height }}
      role="img"
      aria-label="Chart placeholder — visualisation arrives in a later sprint"
    >
      {variant === "bars" ? (
        <div className="flex h-full items-end gap-2.5">
          {BAR_HEIGHTS.map((h, i) => (
            <div
              key={i}
              style={{ height: `${h}%` }}
              className="flex-1 rounded-t-md bg-primary/20 transition-all duration-500 group-hover:bg-primary/30"
            />
          ))}
        </div>
      ) : null}

      {variant === "line" ? (
        <svg className="h-full w-full" viewBox="0 0 200 90" preserveAspectRatio="none">
          <polyline
            points="0,70 28,58 56,64 84,40 112,46 140,26 168,32 200,14"
            fill="none"
            stroke="var(--color-primary)"
            strokeOpacity="0.45"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <polygon
            points="0,70 28,58 56,64 84,40 112,46 140,26 168,32 200,14 200,90 0,90"
            fill="var(--color-primary)"
            fillOpacity="0.08"
          />
        </svg>
      ) : null}

      {variant === "donut" ? (
        <div className="grid h-full place-items-center">
          <div className="relative h-28 w-28 rounded-full border-[14px] border-primary/15 border-t-primary/40 border-r-secondary/40" />
        </div>
      ) : null}

      <span className="absolute right-3 bottom-3 rounded-md border border-border bg-card px-2 py-0.5 text-[10px] font-bold tracking-wide text-muted-foreground uppercase">
        Preview
      </span>
    </div>
  );
}
