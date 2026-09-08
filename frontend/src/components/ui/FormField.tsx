import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  success?: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  success,
  hint,
  children,
  className,
}: FormFieldProps) {
  return (
    <label className={cn("block", className)} htmlFor={htmlFor}>
      <span className="text-caption mb-2 block text-muted">{label}</span>
      {children}
      {hint && !error && !success && (
        <span className="text-caption mt-1 block text-subtle">{hint}</span>
      )}
      {error && (
        <span className="text-caption mt-1 block text-danger" role="alert">
          {error}
        </span>
      )}
      {success && (
        <span className="text-caption mt-1 block text-success">{success}</span>
      )}
    </label>
  );
}
