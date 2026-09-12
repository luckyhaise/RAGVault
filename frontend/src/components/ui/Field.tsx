import { useId, type InputHTMLAttributes, type ReactNode } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: ReactNode;
  error?: string | null;
}

export function Field({
  label,
  hint,
  error,
  id,
  className = "",
  ...rest
}: FieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="space-y-1">
      <label
        htmlFor={inputId}
        className="block text-xs font-medium uppercase tracking-wider text-slate-700"
      >
        {label}
      </label>
      <input
        id={inputId}
        {...rest}
        aria-invalid={error ? true : undefined}
        className={`w-full rounded-lg border bg-white/70 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition focus:outline-none focus:ring-2 disabled:bg-slate-100 ${
          error
            ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/30"
            : "border-slate-300/70 focus:border-emerald-500 focus:ring-emerald-500/30"
        } ${className}`}
      />
      {error ? (
        <p className="text-xs text-rose-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}
