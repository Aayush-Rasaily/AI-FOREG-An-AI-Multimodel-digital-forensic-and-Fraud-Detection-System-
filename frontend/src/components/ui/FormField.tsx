import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  success?: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  success,
  hint,
  required = false,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn("block", className)}>
      <label className="mb-2 block text-caption font-medium text-muted" htmlFor={htmlFor}>
        {label}
        {required && <span aria-hidden="true" className="text-danger"> *</span>}
      </label>
      {children}
      {hint && !error && !success && (
        <span className="mt-1 block text-caption text-subtle">{hint}</span>
      )}
      {error && (
        <span className="mt-1 flex items-center gap-1 text-caption text-danger" role="alert">
          <AlertCircle aria-hidden="true" size={12} />
          {error}
        </span>
      )}
      {success && (
        <span className="mt-1 flex items-center gap-1 text-caption text-success">
          <CheckCircle2 aria-hidden="true" size={12} />
          {success}
        </span>
      )}
    </div>
  );
}
