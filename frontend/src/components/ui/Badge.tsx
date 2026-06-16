import { clsx } from "clsx";

type AssistantStatus = "active" | "idle" | "review" | "error" | "done";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
}

interface StatusBadgeProps {
  status: AssistantStatus;
  className?: string;
}

const statusConfig: Record<AssistantStatus, { label: string; className: string }> = {
  active: {
    label: "활성",
    className: "bg-[#1A1918] text-white",
  },
  idle: {
    label: "대기 중",
    className: "bg-[#EFEFED] text-[#6B6966]",
  },
  review: {
    label: "확인 필요",
    className: "border border-[#2D2B29] text-[#1A1918] bg-transparent",
  },
  error: {
    label: "오류",
    className: "text-[#C0392B]",
  },
  done: {
    label: "완료",
    className: "text-[#6B6966]",
  },
};

export function Badge({ children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-badge px-2 py-0.5 text-[11px] font-medium tracking-wide",
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <Badge className={clsx(config.className, className)}>
      {config.label}
    </Badge>
  );
}

export function StatusDot({ active }: { active: boolean }) {
  return (
    <span
      className={clsx(
        "inline-block h-1.5 w-1.5 rounded-full",
        active ? "bg-[#2D2B29]" : "bg-[#E2E1DE]"
      )}
    />
  );
}
