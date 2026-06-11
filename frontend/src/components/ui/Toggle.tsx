import { clsx } from "clsx";
import type { InputHTMLAttributes } from "react";

interface ToggleProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export function Toggle({ label, className, id, ...props }: ToggleProps) {
  const toggleId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <label htmlFor={toggleId} className={clsx("inline-flex cursor-pointer items-center gap-2", className)}>
      <div className="relative">
        <input type="checkbox" id={toggleId} className="peer sr-only" {...props} />
        <div className="h-5 w-9 rounded-full border border-[#d1d1d1] bg-[#e8e8e8] transition-colors peer-checked:bg-[#0a0a0a] peer-disabled:opacity-50" />
        <div className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
      </div>
      {label && <span className="text-sm text-[#0a0a0a]">{label}</span>}
    </label>
  );
}
