import { cn } from "../../lib/utils";

interface UserAvatarProps {
  name: string;
  className?: string;
  size?: "sm" | "md";
}

export function UserAvatar({ name, className, size = "sm" }: UserAvatarProps) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <div
      aria-hidden="true"
      className={cn(
        "flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 font-semibold text-slate-300",
        size === "sm" ? "h-7 w-7 text-[10px]" : "h-10 w-10 text-xs",
        className,
      )}
      title={name}
    >
      {initials || "U"}
    </div>
  );
}
