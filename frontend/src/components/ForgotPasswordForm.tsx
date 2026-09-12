import { useState, type SubmitEvent } from "react";

import { requestForgotPassword, resetForgottenPassword } from "../api/auth";
import { useToast } from "../context/ToastContext";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import { Field } from "./ui/Field";
import { PASSWORD_RULES_HINT, validateNewPassword, validateOtp } from "../utils/validation";

interface ForgotPasswordFormProps {
  onBackToLogin: () => void;
}

export default function ForgotPasswordForm({ onBackToLogin }: ForgotPasswordFormProps) {
  const toast = useToast();

  const [step, setStep] = useState<"identify" | "reset">("identify");
  const [useEmail, setUseEmail] = useState(false);
  const [userName, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpId, setOtpId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function identifier() {
    return useEmail
      ? { email: email.trim() }
      : { user_name: userName.trim() };
  }

  async function handleRequestCode(event?: SubmitEvent) {
    event?.preventDefault();
    setError(null);

    const value = useEmail ? email.trim() : userName.trim();
    if (!value) {
      setError(useEmail ? "Enter your email address" : "Enter your username");
      return;
    }

    setSubmitting(true);
    try {
      const result = await requestForgotPassword(identifier());
      setOtpId(result.otp_id);
      setOtp("");
      setStep("reset");
      toast.success("Reset code sent to the email on file.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to send code");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReset(event: SubmitEvent) {
    event.preventDefault();
    setError(null);

    const otpError = validateOtp(otp);
    if (otpError) {
      setError(otpError);
      return;
    }
    const passwordError = validateNewPassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setSubmitting(true);
    try {
      await resetForgottenPassword({
        ...identifier(),
        new_password: newPassword,
        otp,
        otp_id: otpId,
      });
      toast.success("Password reset. Please sign in with your new password.");
      onBackToLogin();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to reset password");
    } finally {
      setSubmitting(false);
    }
  }

  if (step === "reset") {
    return (
      <form onSubmit={handleReset} className="space-y-4">
        <div className="mb-2">
          <h3 className="text-xl font-semibold text-slate-800">Set a new password</h3>
          <p className="text-xs text-slate-600">
            Enter the code we emailed you and choose a new password.
          </p>
        </div>

        {error && <Alert type="error" message={error} />}

        <Field
          label="One-time password"
          name="otp"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          value={otp}
          onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))}
          className="text-center font-mono text-lg tracking-[0.5em]"
        />

        <Field
          label="New password"
          name="new_password"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          value={newPassword}
          hint={PASSWORD_RULES_HINT}
          onChange={(event) => setNewPassword(event.target.value)}
        />

        <Button type="submit" loading={submitting} className="w-full">
          {submitting ? "Resetting…" : "Reset password"}
        </Button>

        <button
          type="button"
          onClick={() => {
            setStep("identify");
            setError(null);
          }}
          className="w-full text-center text-xs font-medium text-slate-500 transition hover:text-slate-700 hover:underline"
        >
          ← Start over
        </button>
      </form>
    );
  }

  return (
    <form onSubmit={handleRequestCode} className="space-y-4">
      <div className="mb-2">
        <h3 className="text-xl font-semibold text-slate-800">Forgot password</h3>
        <p className="text-xs text-slate-600">
          We&apos;ll email you a reset code.
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
          autoComplete="username"
          placeholder="Enter your username"
          value={userName}
          onChange={(event) => setUserName(event.target.value)}
        />
      )}

      <div className="text-right">
        <button
          type="button"
          onClick={() => {
            setUseEmail((previous) => !previous);
            setError(null);
          }}
          className="text-xs font-medium text-emerald-700 transition hover:text-emerald-800 hover:underline"
        >
          {useEmail ? "Use username instead" : "Use email instead"}
        </button>
      </div>

      <Button type="submit" loading={submitting} className="w-full">
        {submitting ? "Sending code…" : "Send reset code"}
      </Button>

      <button
        type="button"
        onClick={onBackToLogin}
        className="w-full text-center text-xs font-medium text-slate-500 transition hover:text-slate-700 hover:underline"
      >
        ← Back to sign in
      </button>
    </form>
  );
}
