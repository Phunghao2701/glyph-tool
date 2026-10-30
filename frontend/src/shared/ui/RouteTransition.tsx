import type { ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

export function RouteTransition({ routeKey, children }: { routeKey: string; children: ReactNode }) {
  const reduceMotion = usePrefersReducedMotion();

  return (
    <AnimatePresence initial={false} mode="wait">
      <motion.div
        key={routeKey}
        initial={reduceMotion ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -4 }}
        transition={reduceMotion ? { duration: 0 } : { duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
