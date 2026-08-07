import { Fragment } from "react";
import { motion } from "motion/react";
import { ArrowRight, ArrowDown } from "lucide-react";
import { WORKFLOW_STEPS } from "@/constants/content";

export function WorkflowSection() {
  return (
    <section id="workflow" aria-labelledby="workflow-title" className="scroll-mt-20 py-20">
      <div className="max-w-2xl">
        <p className="text-xs font-bold tracking-[0.2em] text-primary uppercase">
          How it works
        </p>
        <h2 id="workflow-title" className="mt-4 text-3xl text-foreground sm:text-4xl">
          From a single scenario to an infrastructure decision
        </h2>
        <p className="mt-4 text-base text-muted-foreground">
          Five connected stages take raw collision context through prediction, spatial
          analysis and risk scoring into a report your team can act on.
        </p>
      </div>

      <ol className="mt-12 flex flex-col items-stretch gap-2 lg:flex-row lg:items-center">
        {WORKFLOW_STEPS.map((step, index) => (
          <Fragment key={step.title}>
            <motion.li
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.07, ease: "easeOut" }}
              className="flex flex-1 flex-col gap-3 self-stretch rounded-xl border border-border bg-card p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-card"
            >
              <div className="flex items-center gap-2.5">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-border bg-muted/50">
                  <step.icon className="h-4 w-4 text-primary" aria-hidden />
                </span>
                <span className="text-xs font-bold tracking-wide text-muted-foreground uppercase">
                  Step {index + 1}
                </span>
              </div>
              <h3 className="text-sm text-foreground">{step.title}</h3>
              <p className="text-sm text-muted-foreground">{step.body}</p>
            </motion.li>

            {index < WORKFLOW_STEPS.length - 1 ? (
              <li className="grid shrink-0 place-items-center py-1 lg:px-1 lg:py-0" aria-hidden>
                <ArrowDown className="h-4 w-4 text-muted-foreground lg:hidden" />
                <ArrowRight className="hidden h-4 w-4 text-muted-foreground lg:block" />
              </li>
            ) : null}
          </Fragment>
        ))}
      </ol>
    </section>
  );
}
