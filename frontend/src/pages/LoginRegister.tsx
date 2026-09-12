import { useState } from "react";

import CreateAccountForm from "../components/CreateAccountForm";
import ForgotPasswordForm from "../components/ForgotPasswordForm";
import LoginForm from "../components/LoginAccount";
import { VaultIcon } from "../components/ui/Icons";

type Mode = "login" | "register" | "forgot";

const CARD_COPY: Record<Mode, { title: string; prompt: string; action: string }> = {
  login: {
    title: "Secure Digital Repository",
    prompt: "Don't have an account?",
    action: "Create one for free",
  },
  register: {
    title: "Create your vault",
    prompt: "Already have an account?",
    action: "Log in",
  },
  forgot: {
    title: "Recover access",
    prompt: "Remembered it after all?",
    action: "Back to log in",
  },
};

export function LoginRegister() {
  const [mode, setMode] = useState<Mode>("login");

  function toggleFromLogin() {
    setMode((current) => (current === "login" ? "register" : "login"));
  }

  const copy = CARD_COPY[mode];

  return (
    <div className="flex min-h-screen flex-col items-center justify-between bg-gradient-to-br from-emerald-100 via-teal-50 to-slate-100 p-6">
      <header className="mt-8 flex flex-col items-center text-center">
        <span className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/70 text-emerald-700 shadow-sm backdrop-blur">
          <VaultIcon className="h-7 w-7" />
        </span>
        <h1 className="text-4xl font-bold tracking-tight text-slate-800">Ragvault</h1>
        <p className="mt-1 text-sm text-slate-600">{copy.title}</p>
      </header>

      <div className="flex w-full flex-1 items-center justify-center py-8">
        <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white/50 p-8 shadow-xl backdrop-blur-md">
          {mode === "login" && (
            <LoginForm onForgotPassword={() => setMode("forgot")} />
          )}
          {mode === "register" && (
            <CreateAccountForm onGoToLogin={() => setMode("login")} />
          )}
          {mode === "forgot" && (
            <ForgotPasswordForm onBackToLogin={() => setMode("login")} />
          )}

          {mode !== "forgot" && (
            <p className="mt-6 text-center text-xs text-slate-600">
              {copy.prompt}{" "}
              <button
                type="button"
                onClick={toggleFromLogin}
                className="font-semibold text-emerald-700 transition hover:text-emerald-800 hover:underline"
              >
                {copy.action}
              </button>
            </p>
          )}
        </div>
      </div>

      <footer className="pb-2 font-mono text-[10px] uppercase tracking-widest text-slate-500">
        © 2026 Ragvault Inc.
      </footer>
    </div>
  );
}
