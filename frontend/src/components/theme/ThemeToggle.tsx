import { Monitor, Moon, Sun } from "lucide-react";

import { useTheme, type ThemePreference } from "../../theme/ThemeProvider";
import { Button } from "../ui/Button";

const options: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { preference, setPreference } = useTheme();

  return (
    <div
      aria-label="Color theme"
      className="inline-flex rounded-md border border-border p-0.5"
      role="group"
    >
      {options.map(({ value, label, icon: Icon }) => (
        <Button
          aria-label={label}
          aria-pressed={preference === value}
          key={value}
          onClick={() => setPreference(value)}
          size="sm"
          type="button"
          variant={preference === value ? "primary" : "ghost"}
        >
          <Icon aria-hidden="true" size={14} />
          {!compact && label}
        </Button>
      ))}
    </div>
  );
}
