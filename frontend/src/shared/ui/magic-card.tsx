import { useCallback, type PointerEvent, type ReactNode } from "react";
import { motion, useMotionTemplate, useMotionValue, useSpring } from "motion/react";
import { cn } from "../utils/cn";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";
import "./magic-card.css";

type MagicCardProps = {
  children: ReactNode;
  className?: string;
  gradientSize?: number;
  gradientColor?: string;
  gradientFrom?: string;
  gradientTo?: string;
};

/** Magic UI MagicCard copy-in, adapted for the app tokens and reduced-motion preference. */
export function MagicCard({
  children,
  className,
  gradientSize = 240,
  gradientColor = "rgba(81, 131, 94, .12)",
  gradientFrom = "#7fa98d",
  gradientTo = "#d2bd88",
}: MagicCardProps) {
  const reduceMotion = usePrefersReducedMotion();
  const pointerX = useMotionValue(-gradientSize);
  const pointerY = useMotionValue(-gradientSize);
  const smoothX = useSpring(pointerX, { stiffness: 250, damping: 30, mass: 0.6 });
  const smoothY = useSpring(pointerY, { stiffness: 250, damping: 30, mass: 0.6 });
  const border = useMotionTemplate`linear-gradient(var(--magic-card-surface, #fffefa) 0 0) padding-box, radial-gradient(${gradientSize}px circle at ${smoothX}px ${smoothY}px, ${gradientFrom}, ${gradientTo}, var(--magic-card-border, #dfe3dc) 100%) border-box`;
  const spotlight = useMotionTemplate`radial-gradient(${gradientSize}px circle at ${smoothX}px ${smoothY}px, ${gradientColor}, transparent 100%)`;

  const handlePointerMove = useCallback((event: PointerEvent<HTMLDivElement>) => {
    if (event.pointerType !== "mouse") return;
    const bounds = event.currentTarget.getBoundingClientRect();
    pointerX.set(event.clientX - bounds.left);
    pointerY.set(event.clientY - bounds.top);
  }, [pointerX, pointerY]);

  const resetPointer = useCallback(() => {
    pointerX.set(-gradientSize);
    pointerY.set(-gradientSize);
  }, [gradientSize, pointerX, pointerY]);

  if (reduceMotion) {
    return <div className={cn("magic-card", "magic-card-static", className)}>{children}</div>;
  }

  return (
    <motion.div
      className={cn("magic-card", className)}
      onPointerMove={handlePointerMove}
      onPointerLeave={resetPointer}
      style={{ background: border }}
    >
      <motion.div className="magic-card-spotlight" style={{ background: spotlight }} aria-hidden="true" />
      <div className="magic-card-content">{children}</div>
    </motion.div>
  );
}
