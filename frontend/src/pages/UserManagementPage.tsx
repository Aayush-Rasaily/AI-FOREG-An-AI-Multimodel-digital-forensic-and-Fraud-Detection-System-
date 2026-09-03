import { type FormEvent, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { ErrorState } from "../components/ui/ErrorState";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { Select } from "../components/ui/Select";
import {
  useCreateUserMutation,
  useDeleteUserMutation,
  useRolesQuery,
  useUpdateUserMutation,
  useUsersQuery,
} from "../hooks/useAuth";
import { ApiClientError } from "../services/api/client";

export function UserManagementPage() {
  const usersQuery = useUsersQuery(true);
  const rolesQuery = useRolesQuery(true);
  const createUser = useCreateUserMutation();
  const updateUser = useUpdateUserMutation();
  const deleteUser = useDeleteUserMutation();
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [roleName, setRoleName] = useState("Investigator");
  const [error, setError] = useState<string | null>(null);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await createUser.mutateAsync({
        username,
        display_name: displayName,
        password,
        role_names: [roleName],
      });
      setUsername("");
      setDisplayName("");
      setPassword("");
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Unable to create user.",
      );
    }
  }

  return (
    <div>
      <PageHeader
        description="Create accounts, assign roles, and deactivate users."
        eyebrow="Administration"
        title="User Management"
      />
      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Create user</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onCreate}>
              <Input
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Username"
                required
                value={username}
              />
              <Input
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Display name"
                required
                value={displayName}
              />
              <Input
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Temporary password"
                required
                type="password"
                value={password}
              />
              <Select
                onChange={(event) => setRoleName(event.target.value)}
                value={roleName}
              >
                {(rolesQuery.data || ["Investigator"]).map((role) => {
                  const name = typeof role === "string" ? role : role.name;
                  return (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  );
                })}
              </Select>
              {error && <p className="text-xs text-red-300">{error}</p>}
              <Button
                disabled={createUser.isPending}
                size="sm"
                type="submit"
                variant="primary"
              >
                Create user
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Directory</CardTitle>
          </CardHeader>
          <CardContent>
            {usersQuery.isLoading && <LoadingState label="Loading users" />}
            {usersQuery.isError && (
              <ErrorState description="Users could not be loaded." title="Error" />
            )}
            {usersQuery.data && (
              <ul className="space-y-2">
                {usersQuery.data.items.map((user) => (
                  <li
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 px-3 py-3"
                    key={user.id}
                  >
                    <div>
                      <p className="text-sm text-slate-100">
                        {user.display_name}{" "}
                        <span className="text-slate-500">@{user.username}</span>
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {user.roles.map((role) => (
                          <Badge key={role} tone="cyan">
                            {role}
                          </Badge>
                        ))}
                        {!user.is_active && <Badge tone="red">Inactive</Badge>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Select
                        aria-label={`Role for ${user.username}`}
                        defaultValue={user.roles[0] || "Viewer"}
                        onChange={(event) =>
                          void updateUser.mutateAsync({
                            userId: user.id,
                            payload: { role_names: [event.target.value] },
                          })
                        }
                      >
                        {(rolesQuery.data || []).map((role) => (
                          <option key={role.id} value={role.name}>
                            {role.name}
                          </option>
                        ))}
                      </Select>
                      {user.is_active && (
                        <Button
                          onClick={() => void deleteUser.mutateAsync(user.id)}
                          size="sm"
                          variant="danger"
                        >
                          Deactivate
                        </Button>
                      )}
                    </div>
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
