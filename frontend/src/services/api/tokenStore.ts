const ACCESS_KEY = "aiforge.access_token";
const REFRESH_KEY = "aiforge.refresh_token";

let memoryAccess: string | null = null;
let memoryRefresh: string | null = null;

function storage(remember: boolean): Storage {
  return remember ? window.localStorage : window.sessionStorage;
}

export function setTokens(
  accessToken: string,
  refreshToken: string,
  rememberMe: boolean,
): void {
  memoryAccess = accessToken;
  memoryRefresh = refreshToken;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.sessionStorage.removeItem(ACCESS_KEY);
  window.sessionStorage.removeItem(REFRESH_KEY);
  storage(rememberMe).setItem(ACCESS_KEY, accessToken);
  storage(rememberMe).setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens(): void {
  memoryAccess = null;
  memoryRefresh = null;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.sessionStorage.removeItem(ACCESS_KEY);
  window.sessionStorage.removeItem(REFRESH_KEY);
}

export function getAccessToken(): string | null {
  return (
    memoryAccess ||
    window.localStorage.getItem(ACCESS_KEY) ||
    window.sessionStorage.getItem(ACCESS_KEY)
  );
}

export function getRefreshToken(): string | null {
  return (
    memoryRefresh ||
    window.localStorage.getItem(REFRESH_KEY) ||
    window.sessionStorage.getItem(REFRESH_KEY)
  );
}

export function hasRememberedSession(): boolean {
  return window.localStorage.getItem(ACCESS_KEY) != null;
}
