import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { templatesApi, type Template } from "@/api/templates";
import { CatIllustration } from "@/components/cat/CatIllustration";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const CONNECTOR_ICON: Record<string, string> = {
  youtube: "▶",
  gmail: "✉",
  google_drive: "△",
  slack: "◆",
  notion: "◻",
};

const CONNECTOR_FILTER = [
  { value: "", label: "전체" },
  { value: "youtube", label: "YouTube" },
  { value: "gmail", label: "Gmail" },
  { value: "google_drive", label: "Google Drive" },
];

function TemplateCard({ template }: { template: Template }) {
  const qc = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const install = useMutation({
    mutationFn: () => templatesApi.install(template.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assistants"] });
      setConfirming(false);
    },
  });

  return (
    <div className="rounded-card border border-[#e8e8e8] bg-white p-5 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <CatIllustration state="idle" size={32} />
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-semibold text-[#0a0a0a]">{template.name}</h3>
              {template.is_official && (
                <span className="text-[10px] border border-[#0a0a0a] rounded-badge px-1.5 py-0.5 text-[#0a0a0a]">
                  공식
                </span>
              )}
            </div>
            <p className="text-xs text-[#9a9a9a]">설치 {template.install_count.toLocaleString()}회</p>
          </div>
        </div>
      </div>

      <p className="text-sm text-[#5c5c5c] line-clamp-2 flex-1">
        {template.description ?? "설명이 없습니다."}
      </p>

      {/* Required connectors */}
      {template.required_connectors?.length > 0 && (
        <div>
          <p className="text-xs text-[#9a9a9a] mb-1.5">필요 앱</p>
          <div className="flex gap-1.5">
            {template.required_connectors.map((c) => (
              <span
                key={c}
                title={c}
                className="flex h-6 w-6 items-center justify-center rounded-badge border border-[#e8e8e8] text-xs text-[#5c5c5c]"
              >
                {CONNECTOR_ICON[c] ?? "◆"}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Install */}
      <div className="pt-1 border-t border-[#e8e8e8]">
        {confirming ? (
          <div className="space-y-3">
            <p className="text-xs text-[#5c5c5c]">
              설치 후 권한 설정에서 각 액션의 승인 방식을 직접 설정해야 합니다.
            </p>
            <div className="flex gap-2">
              <Button size="sm" loading={install.isPending} onClick={() => install.mutate()}>
                설치 확인
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>
                취소
              </Button>
            </div>
          </div>
        ) : (
          <Button size="sm" variant="secondary" onClick={() => setConfirming(true)}>
            설치하기
          </Button>
        )}
      </div>
    </div>
  );
}

export default function Marketplace() {
  const [q, setQ] = useState("");
  const [connector, setConnector] = useState("");

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["templates", q, connector],
    queryFn: () =>
      templatesApi.list({ q: q || undefined, connector: connector || undefined }),
  });

  const official = templates.filter((t) => t.is_official);
  const community = templates.filter((t) => !t.is_official);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-[#0a0a0a]">마켓플레이스</h1>
        <p className="text-sm text-[#9a9a9a] mt-0.5">검증된 비서 템플릿을 설치해 바로 사용해보세요.</p>
      </div>

      {/* Search + filter */}
      <div className="flex gap-3 items-end">
        <div className="flex-1 max-w-sm">
          <Input
            placeholder="템플릿 검색..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <div className="flex gap-1">
          {CONNECTOR_FILTER.map((f) => (
            <button
              key={f.value}
              onClick={() => setConnector(f.value)}
              className={`px-3 py-1.5 rounded-button text-xs transition-colors border ${
                connector === f.value
                  ? "bg-[#0a0a0a] text-white border-[#0a0a0a]"
                  : "border-[#e8e8e8] text-[#5c5c5c] hover:border-[#d1d1d1]"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-52 rounded-card border border-[#e8e8e8] bg-white animate-pulse" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16">
          <CatIllustration state="watching" size={64} />
          <p className="text-sm text-[#9a9a9a]">검색 결과가 없어요.</p>
        </div>
      ) : (
        <>
          {official.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-[#0a0a0a]">공식 템플릿</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {official.map((t) => (
                  <TemplateCard key={t.id} template={t} />
                ))}
              </div>
            </section>
          )}

          {community.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-[#0a0a0a]">커뮤니티 템플릿</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {community.map((t) => (
                  <TemplateCard key={t.id} template={t} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
