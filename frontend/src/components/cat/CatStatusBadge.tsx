import { clsx } from "clsx";
import { CAT_STATE_TEXT, CatIllustration, type CatState } from "./CatIllustration";

interface CatStatusBadgeProps {
  state: CatState;
  assistantName?: string;
  className?: string;
}

export function CatStatusBadge({ state, assistantName, className }: CatStatusBadgeProps) {
  const text = assistantName
    ? `${assistantName}이(가) ${CAT_STATE_TEXT[state]}`
    : CAT_STATE_TEXT[state];

  return (
    <div className={clsx("inline-flex items-center gap-2", className)}>
      <CatIllustration state={state} size={24} />
      <span className="text-sm text-[#5c5c5c]">{text}</span>
    </div>
  );
}
