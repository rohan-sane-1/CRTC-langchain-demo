"use client";

import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onCredential(credential: string) {
    try {
      await api("/auth/google", { method: "POST", body: JSON.stringify({ credential }) });
      router.replace("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Login failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center gap-6 p-6">
      <h1 className="text-2xl font-semibold">CRTC Proceeding Copilot</h1>
      <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? ""}>
        <GoogleLogin
          onSuccess={(r) => r.credential && onCredential(r.credential)}
          onError={() => setError("Google sign-in failed")}
        />
      </GoogleOAuthProvider>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </main>
  );
}
