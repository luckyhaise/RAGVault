import { useState, type SubmitEvent } from "react";

import { changePassword } from "../api/auth";
import { useToast } from "../context/ToastContext";
import { Alert } from "./StatusMessage";
import { Button } from "./ui/Button";
import { Field } from "./ui/Field";
import { PASSWORD_RULES_HINT, validateNewPassword } from "../utils/validation";

interface ChangePasswordFormProps {
  onSuccess: () => void;
}

export default function ChangePasswordForm({ onSuccess }: ChangePasswordFormProps) {
  const toast = useToast();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setError(null);

    if (!oldPassword) {
      setError("Enter your current password");
      return;
    }
    const passwordError = validateNewPassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }

    setSubmitting(true);
    try {
      await changePassword({ old_password: oldPassword, new_password: newPassword });
      toast.success("Password updated successfully.");
      onSuccess();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to change password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <Alert type="error" message={error} />}

      <Field
        label="Current password"
        name="old_password"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={oldPassword}
        onChange={(event) => setOldPassword(event.target.value)}
      />

      <Field
        label="New password"
        name="new_password"
        type="password"
        autoComplete="new-password"
        placeholder="••••••••"
        hint={PASSWORD_RULES_HINT}
        value={newPassword}
        onChange={(event) => setNewPassword(event.target.value)}
      />

      <Field
        label="Confirm new password"
        name="confirm_password"
        type="password"
        autoComplete="new-password"
        placeholder="••••••••"
        value={confirmPassword}
        onChange={(event) => setConfirmPassword(event.target.value)}
      />

      <div className="flex justify-end gap-3 pt-2">
        <Button type="submit" loading={submitting}>
          {submitting ? "Updating…" : "Update password"}
        </Button>
      </div>
    </form>
  );
}
