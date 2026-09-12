import { useState, type SubmitEvent } from "react";

import { requestCreateAccount, verifyAndCreateAccount } from "../api/auth";
import { useToast } from "../context/ToastContext";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import { Field } from "./ui/Field";
import {
  PASSWORD_RULES_HINT,
  validateEmail,
  validateName,
  validateNewPassword,
  validateOtp,
  
  validateUserName,
} from "../utils/validation";

interface CreateAccountFormProps {
  onGoToLogin: () => void;
}

interface DetailsState {
  name: string;
  user_name: string;
  email: string;
  
  password: string;
}

type DetailErrors = Partial<Record<keyof DetailsState, string>>;

const EMPTY_DETAILS: DetailsState = {
  name: "",
  user_name: "",
  email: "",
  
  password: "",
};

export default function CreateAccountForm({ onGoToLogin }: CreateAccountFormProps) {
  const toast = useToast();

  const [step, setStep] = useState<"details" | "otp">("details");
  const [details, setDetails] = useState<DetailsState>(EMPTY_DETAILS);
  const [fieldErrors, setFieldErrors] = useState<DetailErrors>({});
  const [otpId, setOtpId] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function updateField(key: keyof DetailsState, value: string) {
    setDetails((previous) => ({ ...previous, [key]: value }));
  }

  function validateDetails(): boolean {
    const errors: DetailErrors = {};
    const nameError = validateName(details.name);
    const userNameError = validateUserName(details.user_name);
    const emailError = validateEmail(details.email);
    
    const passwordError = validateNewPassword(details.password);

    if (nameError) errors.name = nameError;
    if (userNameError) errors.user_name = userNameError;
    if (emailError) errors.email = emailError;
    if (passwordError) errors.password = passwordError;

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleRequestOtp(event?: SubmitEvent) {
    event?.preventDefault();
    setError(null);
    if (!validateDetails()) return;

    setSubmitting(true);
    try {
      const result = await requestCreateAccount({
        name: details.name.trim(),
        user_name: details.user_name.trim(),
        email: details.email.trim(),
        password: details.password,
      });
      setOtpId(result.otp_id);
      setOtp("");
      setStep("otp");
      toast.success("Verification code sent to your email.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to send code");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerify(event: SubmitEvent) {
    event.preventDefault();
    setError(null);

    const otpError = validateOtp(otp);
    if (otpError) {
      setError(otpError);
      return;
    }

    setSubmitting(true);
    try {
      await verifyAndCreateAccount({
        ...details,
        name: details.name.trim(),
        user_name: details.user_name.trim(),
        email: details.email.trim(),
        otp_id: otpId,
        otp,
      });
      toast.success("Account created. Please sign in to continue.");
      onGoToLogin();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Verification failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (step === "otp") {
    return (
      <form onSubmit={handleVerify} className="space-y-4">
        <div className="mb-2">
          <h3 className="text-xl font-semibold text-slate-800">Verify your email</h3>
          <p className="text-xs text-slate-600">
            Enter the 6-digit code we sent to {details.email}.
          </p>
        </div>

        {error && <Alert type="error" message={error} />}

        <Field
          label="One-time password"
          name="otp"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="000000"
          value={otp}
          onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))}
          className="text-center font-mono text-lg tracking-[0.5em]"
        />

        <div className="text-center text-xs text-slate-600">
          Didn&apos;t get the code?{" "}
          <button
            type="button"
            disabled={submitting}
            onClick={() => handleRequestOtp()}
            className="font-semibold text-emerald-700 transition hover:text-emerald-800 hover:underline disabled:opacity-60"
          >
            Resend code
          </button>
        </div>

        <Button type="submit" loading={submitting} className="w-full">
          {submitting ? "Verifying…" : "Verify & create account"}
        </Button>

        <button
          type="button"
          onClick={() => {
            setStep("details");
            setError(null);
          }}
          className="w-full text-center text-xs font-medium text-slate-500 transition hover:text-slate-700 hover:underline"
        >
          ← Use different details
        </button>
      </form>
    );
  }

  return (
    <form onSubmit={handleRequestOtp} className="space-y-4">
      <div className="mb-2">
        <h3 className="text-xl font-semibold text-slate-800">Get started</h3>
        <p className="text-xs text-slate-600">
          Create your secure Ragvault archive today.
        </p>
      </div>

      {error && <Alert type="error" message={error} />}

      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Full name"
          name="name"
          placeholder="John Doe"
          value={details.name}
          error={fieldErrors.name}
          onChange={(event) => updateField("name", event.target.value)}
        />
        <Field
          label="Username"
          name="user_name"
          placeholder="johndoe"
          value={details.user_name}
          error={fieldErrors.user_name}
          onChange={(event) => updateField("user_name", event.target.value)}
        />
      </div>

      <Field
        label="Email address"
        name="email"
        type="email"
        placeholder="you@example.com"
        value={details.email}
        error={fieldErrors.email}
        onChange={(event) => updateField("email", event.target.value)}
      />


      <Field
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        placeholder="••••••••"
        value={details.password}
        error={fieldErrors.password}
        hint={PASSWORD_RULES_HINT}
        onChange={(event) => updateField("password", event.target.value)}
      />

      <Button type="submit" loading={submitting} className="mt-4 w-full">
        {submitting ? "Sending code…" : "Create account"}
      </Button>
    </form>
  );
}
