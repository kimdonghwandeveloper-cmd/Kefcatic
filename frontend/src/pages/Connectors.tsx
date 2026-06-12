import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectorsApi, type ConnectorCredential } from "@/api/connectors";
import { Button } from "@/components/ui/Button";

const CONNECTOR_META: Record<string, { label: string; icon: string; desc: string }> = {
  youtube: { label: "YouTube", icon: "▶", desc: "댓글 읽기 · 답글 작성 · 영상 관리" },
  gmail: { label: "Gmail", desc: "메일 읽기 · 답장 작성 · 레이블 관리", icon: "✉" },
  google_drive: { label: "Google Drive", desc: "파일 읽기 · 문서 생성", icon: "△" },
};

const AUTH_URL_FN: Record<string, () => Promise<{ url: string }>> = {
  youtube: connectorsApi.youtubeAuthUrl,
  gmail: connectorsApi.gmailAuthUrl,
  google_drive: connectorsApi.googleDriveAuthUrl,
};

function ConnectorCard({
  type,
  credential,
  onConnect,
  onDisconnect,
}: {
  type: string;
  credential?: ConnectorCredential;
  onConnect: (type: string) => void;
  onDisconnect: (id: string) => void;
}) {
  const meta = CONNECTOR_META[type] ?? { label: type, icon: "◆", desc: "" };
  const connected = !!credential;

  const timeSince = credential?.created_at
    ? (() => {
        const diff = Date.now() - new Date(credential.created_at).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}분 전`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}시간 전`;
        return `${Math.floor(hrs / 24)}일 전`;
      })()
    : null;

  return (
    <div className="rounded-card border border-[#e8e8e8] bg-white p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-button border border-[#e8e8e8] text-lg">
            {meta.icon}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#0a0a0a]">{meta.label}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-[#0a0a0a]" : "bg-[#d1d1d1]"}`}
              />
              <span className="text-xs text-[#9a9a9a]">{connected ? "연결됨" : "연결 안 됨"}</span>
            </div>
          </div>
        </div>
      </div>

      <p className="text-xs text-[#9a9a9a]">{meta.desc}</p>

      {connected && credential && (
        <div className="space-y-1 text-xs text-[#5c5c5c]">
          {credential.scopes && (
            <p>권한: {credential.scopes.slice(0, 3).join(", ")}</p>
          )}
          {timeSince && <p>연결: {timeSince}</p>}
        </div>
      )}

      <div className="flex gap-2 pt-1 border-t border-[#e8e8e8]">
        {connected ? (
          <>
            <Button size="sm" variant="secondary" onClick={() => onConnect(type)}>
              재연결
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => credential && onDisconnect(credential.id)}
            >
              연결 해제
            </Button>
          </>
        ) : (
          <Button size="sm" onClick={() => onConnect(type)}>
            연결하기
          </Button>
        )}
      </div>
    </div>
  );
}

export default function Connectors() {
  const qc = useQueryClient();

  const { data: credentials = [] } = useQuery({
    queryKey: ["connectors"],
    queryFn: connectorsApi.list,
  });

  const disconnect = useMutation({
    mutationFn: (id: string) => connectorsApi.disconnect(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connectors"] }),
  });

  const handleConnect = async (type: string) => {
    const fn = AUTH_URL_FN[type];
    if (!fn) return;
    try {
      const { url } = await fn();
      window.location.href = url;
    } catch {
      // auth-url endpoint not wired yet
      alert(`${type} 연결은 백엔드 설정 후 사용할 수 있습니다.`);
    }
  };

  const credentialByType = Object.fromEntries(
    credentials.map((c) => [c.connector_type, c])
  );

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#0a0a0a]">앱 연결</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Object.keys(CONNECTOR_META).map((type) => (
          <ConnectorCard
            key={type}
            type={type}
            credential={credentialByType[type]}
            onConnect={handleConnect}
            onDisconnect={(id) => disconnect.mutate(id)}
          />
        ))}
      </div>
    </div>
  );
}
