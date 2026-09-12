import { useState, type SubmitEvent } from "react";

import { useAuth } from "../context/AuthContext";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import { Field } from "./ui/Field";

interface LoginFormProps {
  onForgotPassword: () => void;
}

export default function LoginForm({ onForgotPassword }: LoginFormProps) {
  const { signIn } = useAuth();

  const [useEmail, setUseEmail] = useState(false);
  const [userName, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setError(null);

    const identifier = useEmail ? email.trim() : userName.trim();
    if (!identifier) {
      setError(useEmail ? "Enter your email address" : "Enter your username");
      return;
    }
    if (!password) {
      setError("Enter your password");
      return;
    }

    setSubmitting(true);
    try {
      await signIn(
        useEmail
          ? { email: identifier, password }
          : { user_name: identifier, password },
      );
      // On success the AuthProvider flips to the authenticated view.
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="mb-2">
        <h3 className="text-xl font-semibold text-slate-800">Welcome back</h3>
        <p className="text-xs text-slate-600">
          Sign in using your Ragvault {useEmail ? "email" : "username"}.
        </p>
      </div>

      {error && <Alert type="error" message={error} />}

      {useEmail ? (
        <Field
          label="Email address"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      ) : (
        <Field
          label="Username"
          name="user_name"
          type="text"
          autoComplete="username"
          placeholder="Enter your username"
          value={userName}
          onChange={(event) => setUserName(event.target.value)}
        />
      )}

      <Field
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />

      <div className="flex items-center justify-between text-xs">
        <button
          type="button"
          onClick={() => {
            setUseEmail((previous) => !previous);
            setError(null);
          }}
          className="font-medium text-emerald-700 transition hover:text-emerald-800 hover:underline"
        >
          {useEmail ? "Use username instead" : "Use email instead"}
        </button>
        <button
          type="button"
          onClick={onForgotPassword}
          className="font-medium text-slate-500 transition hover:text-slate-700 hover:underline"
        >
          Forgot password?
        </button>
      </div>

      <Button type="submit" loading={submitting} className="mt-2 w-full">
        {submitting ? "Signing in…" : "Log in"}
      </Button>
    </form>
  );
}
