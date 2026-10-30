import { useEffect, useMemo, useRef } from "react";
import { motion, useInView, useMotionValue, useSpring, useTransform } from "motion/react";
import { cn } from "../utils/cn";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

type NumberTickerProps = {
  value: number;
  className?: string;
  decimalPlaces?: number;
  locale?: string;
  minimumIntegerDigits?: number;
};

/** Magic UI NumberTicker, adapted to this app's local typography and reduced-motion settings. */
export function NumberTicker({ value, className, decimalPlaces = 0, locale = "vi-VN", minimumIntegerDigits = 1 }: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduceMotion = usePrefersReducedMotion();
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { damping: 72, stiffness: 180, mass: 0.8 });
  const formatter = useMemo(() => new Intl.NumberFormat(locale, {
    minimumIntegerDigits,
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
  }), [decimalPlaces, locale, minimumIntegerDigits]);
  const displayValue = useTransform(springValue, latest => formatter.format(Number(latest.toFixed(decimalPlaces))));

  useEffect(() => {
    if (!inView || reduceMotion) return;
    motionValue.set(value);
  }, [inView, motionValue, reduceMotion, value]);

  return (
    <span ref={ref} className={cn("number-ticker inline-flex tabular-nums tracking-tight", className)} aria-label={formatter.format(value)} aria-live="off">
      {reduceMotion ? formatter.format(value) : <motion.span aria-hidden="true">{displayValue}</motion.span>}
    </span>
  );
}
