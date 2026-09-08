import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";
export type DensityPreference = "comfortable" | "compact";

const THEME_KEY = "ai-forge-theme";
const DENSITY_KEY = "ai-forge-density";

interface ThemeContextValue {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  density: DensityPreference;
  setPreference: (value: ThemePreference) => void;
  setDensity: (value: DensityPreference) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readStoredTheme(): ThemePreference {
  try {
    const value = localStorage.getItem(THEME_KEY);
    if (value === "light" || value === "dark" || value === "system") {
      return value;
    }
  } catch {
    /* ignore */
  }
  return "system";
}

function readStoredDensity(): DensityPreference {
  try {
    const value = localStorage.getItem(DENSITY_KEY);
    if (value === "comfortable" || value === "compact") {
      return value;
    }
  } catch {
    /* ignore */
  }
  return "comfortable";
}

function systemTheme(): ResolvedTheme {
  if (typeof window === "undefined" || !window.matchMedia) {
    return "dark";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyDocumentTheme(
  resolved: ResolvedTheme,
  density: DensityPreference,
): void {
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.dataset.density = density;
  root.style.colorScheme = resolved;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] =
    useState<ThemePreference>(readStoredTheme);
  const [density, setDensityState] =
    useState<DensityPreference>(readStoredDensity);
  const [resolved, setResolved] = useState<ResolvedTheme>(() =>
    preference === "system" ? systemTheme() : preference,
  );

  useEffect(() => {
    const next = preference === "system" ? systemTheme() : preference;
    setResolved(next);
    applyDocumentTheme(next, density);
    try {
      localStorage.setItem(THEME_KEY, preference);
      localStorage.setItem(DENSITY_KEY, density);
    } catch {
      /* ignore */
    }
  }, [density, preference]);

  useEffect(() => {
    if (preference !== "system" || !window.matchMedia) {
      return;
    }
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const next = systemTheme();
      setResolved(next);
      applyDocumentTheme(next, density);
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [density, preference]);

  const setPreference = useCallback((value: ThemePreference) => {
    setPreferenceState(value);
  }, []);

  const setDensity = useCallback((value: DensityPreference) => {
    setDensityState(value);
  }, []);

  const context = useMemo(
    () => ({
      preference,
      resolved,
      density,
      setPreference,
      setDensity,
    }),
    [density, preference, resolved, setDensity, setPreference],
  );

  return (
    <ThemeContext.Provider value={context}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return value;
}
