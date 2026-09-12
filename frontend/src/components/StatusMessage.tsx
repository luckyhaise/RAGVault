import type { ReactNode } from "react";

interface AlertProps {
  type: "success" | "error" | "warning" | "info";
  message: ReactNode;
}

const STYLES: Record<AlertProps["type"], string> = {
  success: "bg-emerald-50 text-emerald-800 border-emerald-200",
  error: "bg-rose-50 text-rose-800 border-rose-200",
  warning: "bg-amber-50 text-amber-800 border-amber-200",
  info: "bg-sky-50 text-sky-800 border-sky-200",
};

export function Alert({ type, message }: AlertProps) {
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm ${STYLES[type]}`}
      role="alert"
    >
      {message}
    </div>
  );
}
