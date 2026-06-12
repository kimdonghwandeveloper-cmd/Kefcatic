import { clsx } from "clsx";

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center">
          <div className="flex flex-col items-center gap-1.5">
            <div
              className={clsx(
                "flex h-6 w-6 items-center justify-center rounded-full border-2 text-xs font-medium transition-colors",
                i < currentStep
                  ? "border-[#0a0a0a] bg-[#0a0a0a] text-white"
                  : i === currentStep
                  ? "border-[#0a0a0a] bg-white text-[#0a0a0a]"
                  : "border-[#d1d1d1] bg-white text-[#9a9a9a]"
              )}
            >
              {i < currentStep ? "✓" : i + 1}
            </div>
            <span
              className={clsx(
                "text-[11px] whitespace-nowrap",
                i === currentStep ? "font-medium text-[#0a0a0a]" : "text-[#9a9a9a]"
              )}
            >
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={clsx(
                "h-px w-12 mb-5 transition-colors",
                i < currentStep ? "bg-[#0a0a0a]" : "bg-[#e8e8e8]"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
