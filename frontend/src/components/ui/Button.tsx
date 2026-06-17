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
    "bg-[#1A1918] text-white hover:bg-[#2D2B29] disabled:bg-[#E2E1DE] disabled:text-[#A8A5A2]",
  secondary:
    "bg-white border border-[#E2E1DE] text-[#1A1918] hover:bg-[#EFEFED] disabled:text-[#A8A5A2]",
  ghost:
    "bg-transparent text-[#1A1918] hover:bg-[#EFEFED] disabled:text-[#A8A5A2]",
  destructive:
    "bg-white border border-[#E2E1DE] text-[#C0392B] hover:border-[#C0392B] hover:bg-[#FFF5F5] disabled:text-[#A8A5A2]",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3.5 text-[13px]",
  md: "h-10 px-5 text-[14px]",
  lg: "h-12 px-7 text-[16px]",
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
        "inline-flex items-center justify-center gap-2 rounded-button font-medium transition-colors duration-fast",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1A1918] focus-visible:ring-offset-2",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading && (
        <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v3m0 12v3M3 12h3m12 0h3" />
        </svg>
      )}
      {children}
    </button>
  );
}
