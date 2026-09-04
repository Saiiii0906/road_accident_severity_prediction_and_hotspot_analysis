import { motion } from "motion/react";
import { VALUE_PILLARS } from "@/constants/content";

export function ValueSection() {
  return (
    <section
      id="capabilities"
      aria-labelledby="why-title"
      className="scroll-mt-20 border-t border-border py-12 sm:py-16"
    >
      <div className="max-w-3xl">
        <p className="text-xs font-bold tracking-[0.2em] text-primary uppercase">Capabilities</p>
        <h2
          id="why-title"
          className="mt-3 text-2xl font-bold tracking-tight text-foreground sm:text-3xl lg:text-4xl"
        >
          Why this platform
        </h2>
      </div>
      <div className="mt-8 grid gap-8 md:grid-cols-3">
        {VALUE_PILLARS.map((pillar, index) => (
          <motion.div
            key={pillar.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.08, ease: "easeOut" }}
            className="space-y-3"
          >
            <span className="grid h-11 w-11 place-items-center rounded-xl border border-border bg-muted/50">
              <pillar.icon className="h-5 w-5 text-primary" aria-hidden />
            </span>
            <h3 className="text-base font-semibold text-foreground">{pillar.title}</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">{pillar.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
