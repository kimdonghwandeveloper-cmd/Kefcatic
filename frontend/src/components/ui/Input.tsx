import { clsx } from "clsx";
import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

const baseInputClass =
  "w-full rounded-button border border-[#d1d1d1] bg-white px-3 text-sm text-[#0a0a0a] placeholder-[#9a9a9a] " +
  "transition-colors focus:border-[#0a0a0a] focus:outline-none disabled:bg-[#f5f5f5] disabled:text-[#9a9a9a]";

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-label text-[#0a0a0a]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(baseInputClass, "h-9", error && "border-[#0a0a0a]", className)}
          {...props}
        />
        {error && <p className="text-caption text-[#0a0a0a]">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-label text-[#0a0a0a]">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={clsx(
            baseInputClass,
            "min-h-[80px] resize-y py-2",
            error && "border-[#0a0a0a]",
            className
          )}
          {...props}
        />
        {error && <p className="text-caption text-[#0a0a0a]">{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";
