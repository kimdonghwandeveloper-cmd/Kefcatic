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

const statusConfig: Record<
  AssistantStatus,
  { label: string; className: string; icon?: string }
> = {
  active: {
    label: "활성",
    className: "bg-[#0a0a0a] text-[#fafafa]",
  },
  idle: {
    label: "대기 중",
    className: "bg-[#e8e8e8] text-[#9a9a9a]",
  },
  review: {
    label: "확인 필요",
    className: "border border-[#0a0a0a] text-[#0a0a0a] bg-transparent",
  },
  error: {
    label: "오류",
    className: "text-[#0a0a0a]",
    icon: "⚠",
  },
  done: {
    label: "완료",
    className: "text-[#5c5c5c]",
    icon: "✓",
  },
};

export function Badge({ children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-badge px-2 py-0.5 text-label font-medium",
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
      {config.icon && <span aria-hidden>{config.icon}</span>}
      {config.label}
    </Badge>
  );
}
