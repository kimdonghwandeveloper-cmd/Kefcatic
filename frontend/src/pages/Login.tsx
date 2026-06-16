import { useState } from "react";
import { IsometricRoom } from "@/components/cat/IsometricRoom";

export default function Login() {
  const [loading, setLoading] = useState(false);

  function handleGoogleLogin() {
    setLoading(true);
    window.location.href = "/api/auth/google";
  }

  return (
    <div className="flex min-h-screen bg-[#F5F4F2]">
      {/* Left: illustration */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center bg-[#EFEFED] border-r border-[#E2E1DE]">
        <div className="flex flex-col items-center gap-6 p-12 max-w-sm text-center">
          <IsometricRoom className="w-full max-w-[320px]" />
          <div>
            <h2 className="font-heading text-[20px] font-semibold text-[#1A1918] mb-2">
              고양이 비서와 함께
            </h2>
            <p className="text-[15px] text-[#6B6966] leading-relaxed">
              반복되는 일들을 비서에게 맡기고<br />
              정말 중요한 일에 집중하세요.
            </p>
          </div>
        </div>
      </div>

      {/* Right: login form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-[360px]">
          <div className="mb-8">
            <h1 className="font-heading text-[28px] font-bold text-[#1A1918] mb-2">Kefcatic</h1>
            <p className="text-[15px] text-[#6B6966]">
              고양이 비서와 함께 반복 작업을 자동화하세요.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="flex w-full items-center justify-center gap-3 rounded-button border border-[#E2E1DE] bg-white px-4 py-3 text-[15px] font-medium text-[#1A1918] shadow-card transition hover:bg-[#EFEFED] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <GoogleIcon />
              {loading ? "연결 중..." : "Google로 로그인"}
            </button>
          </div>

          <p className="mt-6 text-[13px] text-[#A8A5A2] text-center">
            로그인하면 서비스 이용약관 및 개인정보처리방침에 동의한 것으로 간주됩니다.
          </p>
        </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <path d="M17.64 9.2c0-.64-.06-1.26-.16-1.85H9v3.49h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.71-1.58 2.7-3.9 2.7-6.62Z" fill="#4285F4" />
      <path d="M9 18c2.43 0 4.47-.81 5.96-2.18l-2.92-2.26c-.8.54-1.83.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.94v2.33A8.99 8.99 0 0 0 9 18Z" fill="#34A853" />
      <path d="M3.97 10.71A5.41 5.41 0 0 1 3.69 9c0-.59.1-1.17.28-1.71V4.96H.94A9.01 9.01 0 0 0 0 9c0 1.45.35 2.82.94 4.04l3.03-2.33Z" fill="#FBBC05" />
      <path d="M9 3.58c1.32 0 2.5.45 3.44 1.34l2.58-2.58A8.99 8.99 0 0 0 9 0 8.99 8.99 0 0 0 .94 4.96L3.97 7.29C4.68 5.16 6.66 3.58 9 3.58Z" fill="#EA4335" />
    </svg>
  );
}
