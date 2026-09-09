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
      className="flex gap-1 overflow-x-auto overscroll-x-contain border-b border-border pb-px [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="tablist"
    >
      {options.map((option) => (
        <button
          aria-selected={value === option.value}
          className={cn(
            "min-h-11 shrink-0 whitespace-nowrap border-b-2 px-3 py-3 text-caption font-medium duration-fast transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            value === option.value
              ? "border-primary text-primary"
              : "border-transparent text-muted hover:text-foreground",
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
