import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingSkeleton({
  rows = 3,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)} aria-hidden>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex items-center gap-3">
          <Skeleton className="h-9 w-9 shrink-0 rounded-lg" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-3 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("space-y-3 rounded-xl border border-border p-5", className)}
      aria-hidden
    >
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-8 w-28" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}

export function MapSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("rounded-xl border border-border p-4", className)}
      aria-hidden
    >
      <Skeleton className="h-full min-h-[320px] w-full rounded-lg" />
    </div>
  );
}

export function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-3", className)} aria-hidden>
      <Skeleton className="h-3 w-28" />
      <div className="flex h-[180px] items-end gap-2.5">
        {[45, 70, 55, 85, 60, 75, 50].map((h, i) => (
          <Skeleton key={i} style={{ height: `${h}%` }} className="flex-1 rounded-t-md" />
        ))}
      </div>
    </div>
  );
}

export function TableSkeleton({
  rows = 5,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-2", className)} aria-hidden>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((__, cell) => (
            <Skeleton key={cell} className="h-4 w-full" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function PlaceholderBlock({
  label,
  className,
}: {
  label: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "placeholder-grid relative grid place-items-center rounded-xl border border-dashed border-border bg-muted/30",
        className,
      )}
    >
      <span className="rounded-md border border-border bg-card px-3 py-1.5 text-xs font-bold tracking-wide text-muted-foreground uppercase">
        {label}
      </span>
    </div>
  );
}
