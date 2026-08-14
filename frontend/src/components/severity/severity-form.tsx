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

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
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
              <Button type="submit" disabled={isSubmitting}>
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
