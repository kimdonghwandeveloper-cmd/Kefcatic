import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "destructive";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-[#0a0a0a] text-[#fafafa] hover:bg-[#2a2a2a] disabled:bg-[#d1d1d1] disabled:text-[#9a9a9a]",
  secondary:
    "bg-white border border-[#e8e8e8] text-[#0a0a0a] hover:bg-[#f5f5f5] disabled:text-[#9a9a9a]",
  ghost:
    "bg-transparent text-[#0a0a0a] hover:bg-[#f5f5f5] disabled:text-[#9a9a9a]",
  destructive:
    "bg-white border border-[#d1d1d1] text-[#0a0a0a] hover:border-[#0a0a0a] disabled:text-[#9a9a9a]",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-7 px-3 text-xs",
  md: "h-9 px-4 text-sm",
  lg: "h-11 px-6 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-button font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0a0a0a] focus-visible:ring-offset-2",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading && (
        <svg
          className="h-4 w-4 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v3m0 12v3M3 12h3m12 0h3"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
