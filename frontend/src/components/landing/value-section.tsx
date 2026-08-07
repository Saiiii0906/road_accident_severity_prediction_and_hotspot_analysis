import { motion } from "motion/react";
import { VALUE_PILLARS } from "@/constants/content";

export function ValueSection() {
  return (
    <section
      aria-labelledby="why-title"
      className="border-t border-border py-20"
    >
      <h2 id="why-title" className="max-w-2xl text-3xl text-foreground sm:text-4xl">
        Why this platform
      </h2>
      <div className="mt-12 grid gap-10 md:grid-cols-3">
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
            <h3 className="text-base text-foreground">{pillar.title}</h3>
            <p className="text-sm text-muted-foreground">{pillar.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
