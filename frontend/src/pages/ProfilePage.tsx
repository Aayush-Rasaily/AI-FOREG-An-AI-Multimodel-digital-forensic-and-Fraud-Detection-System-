import { type FormEvent, useState } from "react";

import { UserAvatar } from "../components/auth/UserAvatar";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { ErrorState } from "../components/ui/ErrorState";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { useAuth } from "../context/AuthContext";
import {
  useChangePasswordMutation,
  useRevokeSessionMutation,
  useSessionsQuery,
} from "../hooks/useAuth";
import { ApiClientError } from "../services/api/client";

export function ProfilePage() {
  const { user, logout } = useAuth();
  const sessionsQuery = useSessionsQuery(false);
  const changePassword = useChangePasswordMutation();
  const revokeSession = useRevokeSessionMutation();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return <LoadingState label="Loading profile" />;
  }

  async function onChangePassword(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await changePassword.mutateAsync({ currentPassword, newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setMessage("Password updated. Other sessions were revoked.");
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Password update failed.",
      );
    }
  }

  return (
    <div>
      <PageHeader
        actions={
          <Button onClick={() => void logout()} size="sm" variant="secondary">
            Sign out
          </Button>
        }
        description="Account details, password controls, and active sessions."
        eyebrow="Identity"
        title="Profile"
      />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <UserAvatar name={user.display_name} size="md" />
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-400">
            <p>
              <span className="text-slate-500">Username:</span> {user.username}
            </p>
            <p>
              <span className="text-slate-500">Display name:</span>{" "}
              {user.display_name}
            </p>
            <p>
              <span className="text-slate-500">Email:</span>{" "}
              {user.email || "Not set"}
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              {user.roles.map((role) => (
                <Badge key={role} tone="cyan">
                  {role}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Change password</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onChangePassword}>
              <Input
                onChange={(event) => setCurrentPassword(event.target.value)}
                placeholder="Current password"
                required
                type="password"
                value={currentPassword}
              />
              <Input
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="New password"
                required
                type="password"
                value={newPassword}
              />
              {message && (
                <p className="text-xs text-emerald-300">{message}</p>
              )}
              {error && <p className="text-xs text-red-300">{error}</p>}
              <Button
                disabled={changePassword.isPending}
                size="sm"
                type="submit"
                variant="primary"
              >
                Update password
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            {sessionsQuery.isLoading && <LoadingState label="Loading sessions" />}
            {sessionsQuery.isError && (
              <ErrorState description="Sessions could not be loaded." title="Error" />
            )}
            {sessionsQuery.data && (
              <ul className="space-y-2">
                {sessionsQuery.data.items.map((session) => (
                  <li
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 px-3 py-2 text-xs text-slate-400"
                    key={session.id}
                  >
                    <div>
                      <p className="text-slate-200">
                        {session.browser || "Unknown browser"} ·{" "}
                        {session.device_name || "Device"}
                        {session.current ? " (current)" : ""}
                      </p>
                      <p>
                        {session.ip_address || "No IP"} · expires{" "}
                        {new Date(session.expires_at).toLocaleString()}
                      </p>
                    </div>
                    {!session.revoked && !session.current && (
                      <Button
                        onClick={() => void revokeSession.mutateAsync(session.id)}
                        size="sm"
                        variant="danger"
                      >
                        Revoke
                      </Button>
                    )}
                    {session.revoked && <Badge tone="neutral">Revoked</Badge>}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
