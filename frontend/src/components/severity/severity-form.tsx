import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, RotateCcw, Gauge } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Form } from "@/components/ui/form";
import { Separator } from "@/components/ui/separator";
import { AccidentContextSection } from "@/components/severity/accident-context-section";
import { RoadConditionsSection } from "@/components/severity/road-conditions-section";
import { EnvironmentalConditionsSection } from "@/components/severity/environmental-conditions-section";
import {
  severityFormDefaults,
  severityFormSchema,
  type SeverityFormValues,
} from "@/components/severity/severity-schema";
import { predictSeverity } from "@/lib/api/severity";
import { useSearchParams } from "next/navigation";
import { toast } from "@/components/ui/sonner";

interface SeverityFormProps {
  isSubmitting: boolean;
  onSubmit: (values: SeverityFormValues) => void;
  onReset: () => void;
}

export function SeverityForm({ isSubmitting, onSubmit, onReset }: SeverityFormProps) {
  const form = useForm<SeverityFormValues>({
    resolver: zodResolver(severityFormSchema),
    defaultValues: severityFormDefaults as SeverityFormValues,
    mode: "onBlur",
  });

  const navigate = useSearchParams();
  const apiConfigured = import.meta.env.VITE_API_BASE_URL !== undefined;

  const onFormSubmit = async (values: SeverityFormValues) => {
    try {
      const request = {
        accident_date: values.date,
        accident_time: values.time,
        day_of_week: values.dayOfWeek,
        vehicles_involved: values.vehicles,
        casualties: values.casualties,
        speed_limit: Number(values.speedLimit),
        junction_control: values.junctionControl,
        road_type: values.roadType,
        traffic_density: values.trafficDensity,
        road_surface: values.roadSurface,
        weather: values.weather,
        light_conditions: values.lightConditions,
        visibility: values.visibility,
        area_type: values.areaType,
      };

      // Check if backend is configured
      if (!apiConfigured) {
        toast.error("Backend API is not configured. Please set VITE_API_BASE_URL.");
        return;
      }

      const result = await predictSeverity(request);
      
      onSubmit({
        ...values,
        severity: result.severity,
        confidence: result.confidence,
        interpretation: result.interpretation,
        contributingFactors: result.contributingFactors,
        recommendedAction: result.recommendedAction,
        modelVersion: result.modelVersion,
      });
    } catch (error) {
      if (error instanceof Error && error.name === "ApiError") {
        toast.error((error as { code?: string }).code 
          ? `Error ${(error as { code?: string }).code}: ${error.message}`
          : error.message);
      } else {
        toast.error("Unexpected error occurred. Please try again.");
      }
      throw error;
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onFormSubmit)} noValidate>
        <Card className="border-border bg-card shadow-none">
          <CardContent className="space-y-8 p-5 sm:p-6">
            <AccidentContextSection control={form.control} />
            <Separator />
            <RoadConditionsSection control={form.control} />
            <Separator />
            <EnvironmentalConditionsSection control={form.control} />
          </CardContent>
          <CardFooter className="flex flex-col-reverse items-stretch gap-3 border-t border-border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <p className="text-xs text-muted-foreground">
              Fields marked <span className="text-danger">*</span> are required.
            </p>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  form.reset(severityFormDefaults as SeverityFormValues);
                  onReset();
                }}
                disabled={isSubmitting}
              >
                <RotateCcw className="h-4 w-4" aria-hidden />
                Reset
              </Button>
              <Button type="submit" disabled={isSubmitting || !apiConfigured}>
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <Gauge className="h-4 w-4" aria-hidden />
                )}
                {isSubmitting ? "Analyzing…" : "Predict Severity"}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </form>
    </Form>
  );
}