import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/api/auth";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";
import { Divider } from "@/components/ui/Divider";

type Section = "account" | "notifications" | "api";

const SECTIONS: { key: Section; label: string }[] = [
  { key: "account", label: "계정" },
  { key: "notifications", label: "알림" },
  { key: "api", label: "API 키" },
];

function AccountSection() {
  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.getMe,
  });

  return (
    <div className="space-y-6">
      <Card>
        <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4">계정 정보</h3>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.name ?? ""}
                className="h-12 w-12 rounded-full border border-[#e8e8e8]"
              />
            ) : (
              <div className="h-12 w-12 rounded-full bg-[#f5f5f5] border border-[#e8e8e8] flex items-center justify-center text-lg text-[#9a9a9a]">
                {user?.name?.[0] ?? "?"}
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-[#0a0a0a]">{user?.name ?? "-"}</p>
              <p className="text-xs text-[#9a9a9a]">{user?.email}</p>
            </div>
          </div>
          <Divider />
          <div className="space-y-3">
            <Input label="이름" defaultValue={user?.name ?? ""} disabled />
            <Input label="이메일" defaultValue={user?.email ?? ""} disabled />
          </div>
          <p className="text-xs text-[#9a9a9a]">
            계정 정보는 Google / GitHub 로그인으로 관리됩니다.
          </p>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4">연결된 계정</h3>
        <div className="divide-y divide-[#e8e8e8]">
          {[
            { provider: "Google", icon: "G", connected: true },
            { provider: "GitHub", icon: "◆", connected: false },
          ].map((acc) => (
            <div key={acc.provider} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-badge border border-[#e8e8e8] text-xs font-medium text-[#5c5c5c]">
                  {acc.icon}
                </span>
                <span className="text-sm text-[#0a0a0a]">{acc.provider}</span>
              </div>
              {acc.connected ? (
                <span className="text-xs text-[#9a9a9a]">연결됨</span>
              ) : (
                <Button size="sm" variant="secondary">연결하기</Button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function NotificationsSection() {
  const [settings, setSettings] = useState({
    approval_email: true,
    approval_browser: true,
    error_email: true,
    error_browser: false,
    weekly_summary: false,
  });

  const toggle = (key: keyof typeof settings) =>
    setSettings((s) => ({ ...s, [key]: !s[key] }));

  const rows = [
    { key: "approval_email" as const, label: "승인 대기 — 이메일", desc: "새 승인 요청 발생 시" },
    { key: "approval_browser" as const, label: "승인 대기 — 브라우저", desc: "브라우저 내 알림" },
    { key: "error_email" as const, label: "오류 발생 — 이메일", desc: "비서 실행 실패 시" },
    { key: "error_browser" as const, label: "오류 발생 — 브라우저", desc: "브라우저 내 알림" },
    { key: "weekly_summary" as const, label: "주간 요약 이메일", desc: "매주 월요일 오전 9시" },
  ];

  return (
    <Card>
      <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4">알림 설정</h3>
      <div className="divide-y divide-[#e8e8e8]">
        {rows.map((row) => (
          <div key={row.key} className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm text-[#0a0a0a]">{row.label}</p>
              <p className="text-xs text-[#9a9a9a]">{row.desc}</p>
            </div>
            <Toggle
              checked={settings[row.key]}
              onChange={() => toggle(row.key)}
            />
          </div>
        ))}
      </div>
      <div className="mt-4">
        <Button size="sm">저장</Button>
      </div>
    </Card>
  );
}

function ApiSection() {
  const [revealed, setRevealed] = useState(false);
  const fakeKey = "kef_sk_••••••••••••••••••••••••••••••••";
  const realKey = "kef_sk_1a2b3c4d5e6f7g8h9i0j_example_only";

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="text-sm font-semibold text-[#0a0a0a] mb-1">API 키</h3>
        <p className="text-xs text-[#9a9a9a] mb-4">
          외부 서비스나 로컬 에이전트 연동에 사용합니다.
        </p>
        <div className="flex gap-2 items-center">
          <code className="flex-1 rounded-button border border-[#e8e8e8] bg-[#f5f5f5] px-3 py-2 text-xs font-mono text-[#5c5c5c] truncate">
            {revealed ? realKey : fakeKey}
          </code>
          <Button size="sm" variant="secondary" onClick={() => setRevealed((v) => !v)}>
            {revealed ? "숨기기" : "보기"}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => navigator.clipboard.writeText(realKey)}>
            복사
          </Button>
        </div>
        <p className="text-xs text-[#9a9a9a] mt-3">
          API 키는 외부에 노출되지 않도록 주의하세요. 노출 시 즉시 재발급하세요.
        </p>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4">로컬 에이전트</h3>
        <p className="text-xs text-[#9a9a9a] mb-3">
          로컬 파일, 브라우저 자동화가 필요한 경우 데스크톱 에이전트를 설치하세요.
        </p>
        <Button size="sm" variant="secondary" disabled>
          데스크톱 에이전트 다운로드 (Phase 5)
        </Button>
      </Card>
    </div>
  );
}

export default function Settings() {
  const [section, setSection] = useState<Section>("account");

  return (
    <div className="flex gap-8 max-w-3xl">
      {/* Side nav */}
      <nav className="w-40 shrink-0 space-y-0.5">
        {SECTIONS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`w-full text-left px-3 py-2 rounded-button text-sm transition-colors ${
              section === key
                ? "bg-[#f5f5f5] text-[#0a0a0a] font-medium"
                : "text-[#5c5c5c] hover:text-[#0a0a0a]"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {section === "account" && <AccountSection />}
        {section === "notifications" && <NotificationsSection />}
        {section === "api" && <ApiSection />}
      </div>
    </div>
  );
}
