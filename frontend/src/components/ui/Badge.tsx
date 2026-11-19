import { type ReactNode } from "react";
import { clsx } from "clsx";

type BadgeVariant =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "info"
  | "success"
  | "warning"
  | "error"
  | "neutral";

type BadgeSize = "sm" | "md";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  critical: "badge-error text-white",
  high: "bg-orange-500 text-white border-orange-500",
  medium: "badge-warning",
  low: "badge-info",
  info: "badge-ghost",
  success: "badge-success",
  warning: "badge-warning",
  error: "badge-error",
  neutral: "badge-neutral",
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: "badge-sm text-xs",
  md: "badge-md",
};

export function Badge({
  children,
  variant = "neutral",
  size = "md",
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        "badge",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
    >
      {children}
    </span>
  );
}
