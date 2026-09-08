import { Search } from "lucide-react";
import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils";
import { Input } from "./Input";

interface SearchInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function SearchInput({
  className,
  label = "Search",
  ...props
}: SearchInputProps) {
  return (
    <label className="relative block min-w-0 flex-1">
      <span className="sr-only">{label}</span>
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
        size={16}
      />
      <Input className={cn("pl-9", className)} {...props} />
    </label>
  );
}
