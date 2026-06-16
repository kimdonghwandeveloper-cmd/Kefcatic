import { clsx } from "clsx";

interface DividerProps {
  className?: string;
  orientation?: "horizontal" | "vertical";
}

export function Divider({ orientation = "horizontal", className }: DividerProps) {
  if (orientation === "vertical") {
    return <div className={clsx("h-full w-px bg-[#E2E1DE]", className)} />;
  }
  return <div className={clsx("h-px w-full bg-[#E2E1DE]", className)} />;
}
