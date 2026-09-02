import { useState } from "react";
import { ArrowRight, Calendar, Clock, Loader2, MapPin, Navigation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { JourneyAnalyzeRequest } from "@/lib/api/journey";

export interface JourneyFormValues {
  source: string;
  destination: string;
  travelDate: string;
  travelTime: string;
}

export interface JourneyFormErrors {
  source?: string | undefined;
  destination?: string | undefined;
  travelDate?: string | undefined;
  travelTime?: string | undefined;
}

interface JourneyFormProps {
  isLoading: boolean;
  onSubmit: (data: JourneyAnalyzeRequest) => void;
}

function getDefaultDate(): string {
  const now = new Date();
  return now.toISOString().slice(0, 10);
}

function getDefaultTime(): string {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

export function JourneyForm({ isLoading, onSubmit }: JourneyFormProps) {
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [travelDate, setTravelDate] = useState(getDefaultDate());
  const [travelTime, setTravelTime] = useState(getDefaultTime());
  const [errors, setErrors] = useState<JourneyFormErrors>({});

  const validate = (): boolean => {
    const nextErrors: JourneyFormErrors = {};
    if (!source.trim() || source.trim().length < 2) {
      nextErrors.source = "Please enter a valid origin location (min 2 characters).";
    }
    if (!destination.trim() || destination.trim().length < 2) {
      nextErrors.destination = "Please enter a valid destination location (min 2 characters).";
    }
    if (!travelDate) {
      nextErrors.travelDate = "Please select a travel date.";
    }
    if (!travelTime) {
      nextErrors.travelTime = "Please select a travel time.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    onSubmit({
      source: source.trim(),
      destination: destination.trim(),
      travel_date: travelDate,
      travel_time: travelTime,
    });
  };

  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader className="border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <Navigation className="h-5 w-5 text-primary" aria-hidden="true" />
          <CardTitle className="text-lg font-semibold text-foreground">
            Plan Journey Analysis
          </CardTitle>
        </div>
        <CardDescription className="text-sm text-muted-foreground">
          Enter your journey itinerary to evaluate corridor accident risk, historical clusters, and
          safety factors for your planned departure.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          <div className="grid gap-6 md:grid-cols-2">
            {/* Origin */}
            <div className="space-y-2">
              <Label
                htmlFor="source-input"
                className="flex items-center gap-1.5 text-sm font-medium text-foreground"
              >
                <MapPin className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Source location <span className="text-destructive">*</span>
              </Label>
              <Input
                id="source-input"
                type="text"
                placeholder="e.g., London Victoria Station"
                value={source}
                onChange={(e) => {
                  setSource(e.target.value);
                  if (errors.source) setErrors((prev) => ({ ...prev, source: undefined }));
                }}
                disabled={isLoading}
                aria-invalid={Boolean(errors.source)}
                aria-describedby={errors.source ? "source-error" : undefined}
                className={errors.source ? "border-destructive focus-visible:ring-destructive" : ""}
                required
              />
              {errors.source && (
                <p id="source-error" className="text-xs text-destructive">
                  {errors.source}
                </p>
              )}
            </div>

            {/* Destination */}
            <div className="space-y-2">
              <Label
                htmlFor="destination-input"
                className="flex items-center gap-1.5 text-sm font-medium text-foreground"
              >
                <MapPin className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Destination location <span className="text-destructive">*</span>
              </Label>
              <Input
                id="destination-input"
                type="text"
                placeholder="e.g., Heathrow Airport Terminal 5"
                value={destination}
                onChange={(e) => {
                  setDestination(e.target.value);
                  if (errors.destination)
                    setErrors((prev) => ({ ...prev, destination: undefined }));
                }}
                disabled={isLoading}
                aria-invalid={Boolean(errors.destination)}
                aria-describedby={errors.destination ? "destination-error" : undefined}
                className={
                  errors.destination ? "border-destructive focus-visible:ring-destructive" : ""
                }
                required
              />
              {errors.destination && (
                <p id="destination-error" className="text-xs text-destructive">
                  {errors.destination}
                </p>
              )}
            </div>

            {/* Travel Date */}
            <div className="space-y-2">
              <Label
                htmlFor="travel-date-input"
                className="flex items-center gap-1.5 text-sm font-medium text-foreground"
              >
                <Calendar className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Travel date <span className="text-destructive">*</span>
              </Label>
              <Input
                id="travel-date-input"
                type="date"
                value={travelDate}
                onChange={(e) => {
                  setTravelDate(e.target.value);
                  if (errors.travelDate) setErrors((prev) => ({ ...prev, travelDate: undefined }));
                }}
                disabled={isLoading}
                aria-invalid={Boolean(errors.travelDate)}
                aria-describedby={errors.travelDate ? "travel-date-error" : undefined}
                className={
                  errors.travelDate ? "border-destructive focus-visible:ring-destructive" : ""
                }
                required
              />
              {errors.travelDate && (
                <p id="travel-date-error" className="text-xs text-destructive">
                  {errors.travelDate}
                </p>
              )}
            </div>

            {/* Travel Time */}
            <div className="space-y-2">
              <Label
                htmlFor="travel-time-input"
                className="flex items-center gap-1.5 text-sm font-medium text-foreground"
              >
                <Clock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Travel time <span className="text-destructive">*</span>
              </Label>
              <Input
                id="travel-time-input"
                type="time"
                value={travelTime}
                onChange={(e) => {
                  setTravelTime(e.target.value);
                  if (errors.travelTime) setErrors((prev) => ({ ...prev, travelTime: undefined }));
                }}
                disabled={isLoading}
                aria-invalid={Boolean(errors.travelTime)}
                aria-describedby={errors.travelTime ? "travel-time-error" : undefined}
                className={
                  errors.travelTime ? "border-destructive focus-visible:ring-destructive" : ""
                }
                required
              />
              {errors.travelTime && (
                <p id="travel-time-error" className="text-xs text-destructive">
                  {errors.travelTime}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end pt-2">
            <Button type="submit" disabled={isLoading} className="min-w-[180px] font-medium">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                  Analyzing journey...
                </>
              ) : (
                <>
                  Analyze journey safety
                  <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
