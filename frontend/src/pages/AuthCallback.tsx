import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export default function AuthCallback() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    // The JWT only carries the user id (sub), so fetch the full profile from
    // /api/auth/me using the token, then store it.
    (async () => {
      try {
        const res = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to load user");
        const user = await res.json();
        setAuth(
          {
            id: user.id,
            email: user.email,
            name: user.name ?? null,
            avatar_url: user.avatar_url ?? null,
          },
          token
        );
        navigate("/", { replace: true });
      } catch {
        navigate("/login", { replace: true });
      }
    })();
  }, [navigate, setAuth]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#FAFAFA] text-sm text-[#6B7280]">
      로그인 처리 중...
    </div>
  );
}
