"use client";

import { useState, useEffect } from "react";
import { User, UserAPI } from "@/lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { StatusBadge } from "@/components/ui/icon-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Plus } from "lucide-react";
import UserActions from "@/components/dashboard/UserActions";
import { Button } from "@/components/ui/button";

import { formatTimeAgo } from "@/lib/utils";

export function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [activeFilter, setActiveFilter] = useState<"all" | "internal" | "external">("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const router = useRouter();

  const fetchUsers = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await UserAPI.getAll();
      setUsers(data);
      applyFilter(activeFilter, data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = (
    filter: "all" | "internal" | "external",
    userData = users
  ) => {
    setActiveFilter(filter);
    if (filter === "internal") {
      setFilteredUsers(userData.filter((u) => !u.is_external));
    } else if (filter === "external") {
      setFilteredUsers(userData.filter((u) => u.is_external));
    } else {
      setFilteredUsers(userData);
    }
  };

  useEffect(() => {
    fetchUsers();

    const handleRefresh = () => {
      fetchUsers();
    };

    window.addEventListener("dashboard:refresh", handleRefresh);
    return () => window.removeEventListener("dashboard:refresh", handleRefresh);
  }, []);

  return (
    <Card id="users">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Users</CardTitle>
            <CardDescription>Manage platform users</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => router.push("/dashboard/users/new")} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New User
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading users</AlertTitle>
            <AlertDescription>
              There was a problem fetching the users data.
            </AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4)
              .fill(0)
              .map((_, i) => (
                <Skeleton key={`user-skeleton-${i}`} className="h-12 w-full" />
              ))}
          </div>
        ) : (
          <>
            {users.length > 0 ? (
              <>
                <div className="flex gap-2 mb-4">
                  <Button
                    variant={activeFilter === "all" ? "default" : "outline"}
                    size="sm"
                    onClick={() => applyFilter("all")}
                  >
                    All
                  </Button>
                  <Button
                    variant={activeFilter === "internal" ? "default" : "outline"}
                    size="sm"
                    onClick={() => applyFilter("internal")}
                  >
                    Internal
                  </Button>
                  <Button
                    variant={activeFilter === "external" ? "default" : "outline"}
                    size="sm"
                    onClick={() => applyFilter("external")}
                  >
                    External
                  </Button>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      {/* <TableHead>Username</TableHead> */}
                      {/* <TableHead>Email</TableHead> */}
                      <TableHead>Full Name</TableHead>
                      {/* <TableHead>Department</TableHead> */}
                      <TableHead>Job Title</TableHead>
                      <TableHead>Level</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.user_id}>
                        {/* <TableCell className="font-medium">{user.username}</TableCell> */}
                        {/* <TableCell className="font-mono text-xs">{user.email}</TableCell> */}
                        <TableCell className="font-medium">{user.full_name || "—"}</TableCell>
                        {/* <TableCell>{user.department || "—"}</TableCell> */}
                        <TableCell>{user.job_title || "—"}</TableCell>
                        <TableCell>{user.level || "—"}</TableCell>
                        <TableCell>
                          {user.is_external ? (
                            <StatusBadge subtype="warning">External</StatusBadge>
                          ) : (
                            <StatusBadge subtype="info">Internal</StatusBadge>
                          )}
                        </TableCell>
                        <TableCell>
                          <StatusBadge subtype={user.is_active ? "success" : "inactive"}>
                            {user.is_active ? "Active" : "Inactive"}
                          </StatusBadge>
                        </TableCell>
                        <TableCell>
                          {user.created_at ? (
                            <span title={new Date(user.created_at).toLocaleString()}>
                              {formatTimeAgo(user.created_at)}
                            </span>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                        <TableCell>
                          <UserActions user={user} onUpdate={fetchUsers} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {activeFilter !== "all" && filteredUsers.length === 0 && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-md text-center">
                    <p className="text-muted-foreground">
                      No {activeFilter} users found. Try a different filter.
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No users available yet. Click "New User" to create one.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
