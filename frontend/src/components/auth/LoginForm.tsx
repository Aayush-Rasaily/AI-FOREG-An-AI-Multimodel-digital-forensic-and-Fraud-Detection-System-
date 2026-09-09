import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useLoginMutation } from "../../hooks/useAuth";
import { ApiClientError } from "../../services/api/client";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export function LoginForm() {
  const navigate = useNavigate();
  const loginMutation = useLoginMutation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await loginMutation.mutateAsync({
        username,
        password,
        remember_me: rememberMe,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Sign-in failed.");
      }
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <label className="block">
        <span className="mb-2 block text-xs text-muted">Username</span>
        <Input
          autoComplete="username"
          onChange={(event) => setUsername(event.target.value)}
          required
          value={username}
        />
      </label>
      <label className="block">
        <span className="mb-2 block text-xs text-muted">Password</span>
        <Input
          autoComplete="current-password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>
      <label className="flex items-center gap-2 text-xs text-muted">
        <input
          checked={rememberMe}
          className="rounded border-border-strong"
          onChange={(event) => setRememberMe(event.target.checked)}
          type="checkbox"
        />
        Remember me
      </label>
      {error && (
        <p className="rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
          {error}
        </p>
      )}
      <Button
        className="w-full"
        disabled={loginMutation.isPending}
        type="submit"
        variant="primary"
      >
        {loginMutation.isPending ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
