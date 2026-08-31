import { cn } from "../../lib/utils";

export interface TabOption<T extends string> {
  value: T;
  label: string;
  disabled?: boolean;
}

interface TabsProps<T extends string> {
  options: TabOption<T>[];
  value: T;
  onChange: (value: T) => void;
}

export function Tabs<T extends string>({
  options,
  value,
  onChange,
}: TabsProps<T>) {
  return (
    <div
      aria-label="Workspace sections"
      className="flex gap-1 overflow-x-auto border-b border-slate-800"
      role="tablist"
    >
      {options.map((option) => (
        <button
          aria-selected={value === option.value}
          className={cn(
            "whitespace-nowrap border-b-2 px-3 py-3 text-xs font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/80",
            value === option.value
              ? "border-cyan-400 text-cyan-300"
              : "border-transparent text-slate-500 hover:text-slate-300",
          )}
          disabled={option.disabled}
          key={option.value}
          onClick={() => onChange(option.value)}
          role="tab"
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

