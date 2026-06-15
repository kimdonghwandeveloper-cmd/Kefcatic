import { useState } from "react";

export default function Login() {
  const [loading, setLoading] = useState(false);

  function handleGoogleLogin() {
    setLoading(true);
    // Full-page navigation: the backend 307-redirects to Google's consent
    // screen, then redirects back to /auth/callback?token=... after login.
    window.location.href = "/api/auth/google";
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#FAFAFA]">
      <div className="w-full max-w-sm rounded-xl border border-[#E5E7EB] bg-white p-10 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-[#0A0A0A]">Kefcatic</h1>
        <p className="mb-8 text-sm text-[#6B7280]">고양이 비서와 함께 반복 작업을 자동화하세요.</p>

        <div className="flex flex-col gap-3">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2.5 text-sm font-medium text-[#0A0A0A] transition hover:bg-[#F3F4F6] disabled:opacity-50"
          >
            <GoogleIcon />
            {loading ? "연결 중..." : "Google로 로그인"}
          </button>
          {/* GitHub 로그인은 백엔드 라우트 구현 후 노출 */}
        </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M15.68 8.18c0-.57-.05-1.11-.14-1.64H8v3.1h4.31a3.68 3.68 0 0 1-1.6 2.42v2.01h2.59c1.52-1.4 2.4-3.46 2.4-5.9Z"
        fill="#4285F4"
      />
      <path
        d="M8 16c2.16 0 3.97-.72 5.3-1.93l-2.59-2.01c-.71.48-1.63.76-2.71.76-2.08 0-3.84-1.41-4.47-3.3H.86v2.07A8 8 0 0 0 8 16Z"
        fill="#34A853"
      />
      <path
        d="M3.53 9.52A4.8 4.8 0 0 1 3.28 8c0-.53.09-1.04.25-1.52V4.41H.86A8 8 0 0 0 0 8c0 1.29.31 2.51.86 3.59l2.67-2.07Z"
        fill="#FBBC05"
      />
      <path
        d="M8 3.18c1.17 0 2.22.4 3.05 1.19l2.28-2.28A8 8 0 0 0 8 0 8 8 0 0 0 .86 4.41L3.53 6.48C4.16 4.59 5.92 3.18 8 3.18Z"
        fill="#EA4335"
      />
    </svg>
  );
}
