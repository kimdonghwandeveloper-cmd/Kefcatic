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
  "w-full rounded-button border border-[#E2E1DE] bg-white px-3 text-[15px] text-[#1A1918] " +
  "placeholder-[#A8A5A2] transition-colors duration-fast " +
  "focus:border-[#1A1918] focus:outline-none " +
  "disabled:bg-[#F5F4F2] disabled:text-[#A8A5A2]";

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-[#1A1918]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(baseInputClass, "h-9", error && "border-[#C0392B]", className)}
          {...props}
        />
        {error && <p className="text-[11px] text-[#C0392B]">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-[#1A1918]">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={clsx(
            baseInputClass,
            "min-h-[80px] resize-y py-2",
            error && "border-[#C0392B]",
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-[#C0392B]">{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";
