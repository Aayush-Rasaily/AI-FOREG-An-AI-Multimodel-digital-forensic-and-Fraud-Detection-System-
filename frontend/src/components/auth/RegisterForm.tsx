import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useRegisterMutation } from "../../hooks/useAuth";
import { ApiClientError } from "../../services/api/client";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export function RegisterForm() {
  const navigate = useNavigate();
  const registerMutation = useRegisterMutation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!username.trim()) {
      setError("Username cannot be empty.");
      return;
    }
    if (!password) {
      setError("Password cannot be empty.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Password and confirmation do not match.");
      return;
    }
    try {
      await registerMutation.mutateAsync({
        username: username.trim(),
        password,
        confirm_password: confirmPassword,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Registration failed.");
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
          autoComplete="new-password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>
      <label className="block">
        <span className="mb-2 block text-xs text-muted">Confirm password</span>
        <Input
          autoComplete="new-password"
          onChange={(event) => setConfirmPassword(event.target.value)}
          required
          type="password"
          value={confirmPassword}
        />
      </label>
      {error && (
        <p className="rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
          {error}
        </p>
      )}
      <Button
        className="w-full"
        disabled={registerMutation.isPending}
        type="submit"
        variant="primary"
      >
        {registerMutation.isPending ? "Creating account…" : "Register"}
      </Button>
      <p className="text-center text-xs text-muted">
        Already have an account?{" "}
        <Link className="font-medium text-primary hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </form>
  );
}
