const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const appConfig = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
  appName: "AI-FORGE",
  environment: import.meta.env.MODE,
  isProduction: import.meta.env.PROD,
} as const;
