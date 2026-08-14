import { MapPinned, Layers, Navigation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function MapHero() {
  return (
    <Card className="overflow-hidden border-border bg-card shadow-none">
      <CardContent className="p-0">
        <div className="relative">
          <div className="placeholder-grid grid min-h-[380px] place-items-center bg-muted/25 px-6 py-14 lg:min-h-[460px]">
            <div className="max-w-md text-center">
              <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl border border-border bg-card">
                <MapPinned className="h-6 w-6 text-primary" aria-hidden />
              </span>
              <h2 className="mt-5 text-xl text-foreground">Network hotspot map</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Spatial clustering of high-severity incidents across the monitored road network,
                with corridor and junction level drill-down.
              </p>
              <Button variant="outline" size="sm" className="mt-6" disabled>
                Interactive Map Coming Next Sprint
              </Button>
            </div>
          </div>

          <div className="pointer-events-none absolute top-4 left-4 flex flex-col gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card/90">
              <Layers className="h-4 w-4 text-muted-foreground" aria-hidden />
            </span>
            <span className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-card/90">
              <Navigation className="h-4 w-4 text-muted-foreground" aria-hidden />
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
