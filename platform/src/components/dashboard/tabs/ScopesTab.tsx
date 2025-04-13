"use client";

import { useState, useEffect } from "react";
import { Scope, ScopeAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import ScopeActions from "@/components/dashboard/ScopeActions";
import { RegisterScopeDialog } from "@/components/dashboard/RegisterScopeDialog";

export function ScopesTab() {
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchScopes = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await ScopeAPI.getAll();
      setScopes(data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load scopes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScopes();
  }, []);

  return (
    <Card id="scopes">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>OAuth Scopes</CardTitle>
          <CardDescription>Manage available scopes and their permissions</CardDescription>
        </div>
        <RegisterScopeDialog onScopeAdded={fetchScopes} />
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading scopes</AlertTitle>
            <AlertDescription>There was a problem fetching the scopes data.</AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`scope-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <div>
            {scopes.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Options</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scopes.map((scope) => (
                    <TableRow key={scope.scope_id}>
                      <TableCell className="font-medium">{scope.name}</TableCell>
                      <TableCell className="max-w-[300px] truncate">{scope.description}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{scope.category}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {scope.is_default === true && (
                            <Badge variant="secondary" className="text-xs">Default</Badge>
                          )}
                          {scope.is_sensitive === true && (
                            <Badge variant="destructive" className="text-xs">Sensitive</Badge>
                          )}
                          {scope.requires_approval === true && (
                            <Badge variant="outline" className="text-xs">Approval Required</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={scope.is_active !== false ? "default" : "secondary"}>
                          {scope.is_active !== false ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ScopeActions scope={scope} onUpdate={fetchScopes} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                <p className="text-muted-foreground">No scopes registered yet. Click "Register New Scope" to create one.</p>
                <Button 
                  variant="outline" 
                  className="mt-4" 
                  onClick={async () => {
                    try {
                      await ScopeAPI.addDefault();
                      fetchScopes();
                      toast.success("Default scopes added successfully");
                    } catch (error) {
                      toast.error("Failed to add default scopes");
                    }
                  }}
                >
                  Add Default Scopes
                </Button>
              </div>
            )}

            {/* Scope Inheritance Controls */}
            <div className="mt-8 border rounded-lg p-4">
              <h3 className="text-lg font-medium mb-4">Scope Inheritance Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input type="radio" id="inheritance-restricted" name="inheritance" className="h-4 w-4" defaultChecked />
                  <div>
                    <label htmlFor="inheritance-restricted" className="font-medium">Restricted</label>
                    <p className="text-sm text-muted-foreground">Child tokens can only request scopes explicitly granted to parent</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input type="radio" id="inheritance-subset" name="inheritance" className="h-4 w-4" />
                  <div>
                    <label htmlFor="inheritance-subset" className="font-medium">Subset</label>
                    <p className="text-sm text-muted-foreground">Child tokens can request any subset of parent's scopes</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input type="radio" id="inheritance-transitive" name="inheritance" className="h-4 w-4" />
                  <div>
                    <label htmlFor="inheritance-transitive" className="font-medium">Transitive</label>
                    <p className="text-sm text-muted-foreground">Child tokens inherit all parent scopes automatically</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 mt-4">
              <Button variant="outline">Reset to Defaults</Button>
              <Button>Save Changes</Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
