import type { ReactNode } from "react";
import type { ButtonKind } from "../types/ui";
import { cn } from "../utils/cn";
import { Button as ShadcnButton } from "./primitives/button";

type ButtonProps = Omit<React.ComponentProps<typeof ShadcnButton>, "variant"> & {
  children: ReactNode;
  kind?: ButtonKind;
};

const variantMap = {
  primary: "default",
  secondary: "outline",
  quiet: "ghost",
  danger: "destructive",
} as const;

const legacyClass = {
  primary: "btn-primary",
  secondary: "btn-light",
  quiet: "btn-text",
  danger: "btn-danger",
} as const;

export function Button({ children, kind = "secondary", className, ...props }: ButtonProps) {
  return <ShadcnButton variant={variantMap[kind]} className={cn("btn", legacyClass[kind], className)} {...props}>{children}</ShadcnButton>;
}

