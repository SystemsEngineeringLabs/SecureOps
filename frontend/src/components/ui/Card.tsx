import { type ReactNode } from "react";
import { clsx } from "clsx";

type CardPadding = "none" | "sm" | "md" | "lg";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: CardPadding;
  bordered?: boolean;
  shadow?: boolean;
}

const paddingClasses: Record<CardPadding, string> = {
  none: "",
  sm: "p-3",
  md: "p-5",
  lg: "p-8",
};

export function Card({
  children,
  className,
  padding = "md",
  bordered = true,
  shadow = true,
}: CardProps) {
  return (
    <div
      className={clsx(
        "card bg-base-100",
        bordered && "border border-base-200",
        shadow && "shadow-sm",
        className,
      )}
    >
      <div className={clsx("card-body", paddingClasses[padding])}>
        {children}
      </div>
    </div>
  );
}

export function CardHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("mb-4 border-b border-base-200 pb-3", className)}>
      {children}
    </div>
  );
}

export function CardFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("mt-4 border-t border-base-200 pt-3", className)}>
      {children}
    </div>
  );
}
