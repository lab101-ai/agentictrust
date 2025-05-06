"use client";

import { useState, useEffect } from "react";
import { Tool, ToolAPI } from "@/lib/api";
import { Scope, ScopeAPI } from '@/lib/api';
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
// Badge import removed as we're using specialized badge components
import { IconBadge, StatusBadge, ResourceBadge, ScopeBadge } from "@/components/ui/icon-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Check, X, Wrench, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import ToolActions from "@/components/dashboard/ToolActions";

import { formatTimeAgo } from "@/lib/utils";

// Helper function to determine badge subtype based on scope name
const getScopeBadgeSubtype = (scopeName: string): string => {
  const lowerName = scopeName.toLowerCase();
  if (lowerName.includes('read')) return 'read';
  if (lowerName.includes('write')) return 'write';
  if (lowerName.includes('create')) return 'create';
  if (lowerName.includes('delete')) return 'delete';
  if (lowerName.includes('admin')) return 'admin';
  return 'default'; // Fallback subtype
};

export function ToolsTab() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [scopes, setScopes] = useState<Scope[]>([]); // State for scopes
  const [scopeMap, setScopeMap] = useState<Map<string, string>>(new Map()); // State for ID -> name map
  const [filteredTools, setFilteredTools] = useState<Tool[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchTools = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedTools = await ToolAPI.getAll();
      setTools(fetchedTools);
      // Fetch scopes as well
      const fetchedScopes = await ScopeAPI.getAll();
      setScopes(fetchedScopes);
      
      // Create the ID -> name map
      const newScopeMap = new Map<string, string>();
      fetchedScopes.forEach(scope => {
        newScopeMap.set(scope.scope_id, scope.name);
      });
      setScopeMap(newScopeMap);
      applyFilter(activeFilter, fetchedTools);
    } catch (err) {
      console.error("Failed to fetch data:", err);
      setError("Failed to load tools");
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilter = (filter: 'all' | 'active' | 'inactive', toolData = tools) => {
    setActiveFilter(filter);
    switch (filter) {
      case 'active':
        setFilteredTools(toolData.filter(tool => tool.is_active));
        break;
      case 'inactive':
        setFilteredTools(toolData.filter(tool => !tool.is_active));
        break;
      default:
        setFilteredTools(toolData);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  return (
    <Card id="tools">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Tools</CardTitle>
            <CardDescription>Manage tools that agents can use</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={() => router.push('/dashboard/tools/new')} 
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Tool
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading tools</AlertTitle>
            <AlertDescription>There was a problem fetching the tools data.</AlertDescription>
          </Alert>
        ) : isLoading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`tool-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            {tools.length > 0 ? (
              <>
                <div className="flex gap-2 mb-4">
                  <Button 
                    variant={activeFilter === 'all' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('all')}
                  >
                    All
                  </Button>
                  <Button 
                    variant={activeFilter === 'active' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('active')}
                  >
                    Active
                  </Button>
                  <Button 
                    variant={activeFilter === 'inactive' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => applyFilter('inactive')}
                  >
                    Inactive
                  </Button>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Tool ID</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTools.map((tool) => (
                      <TableRow key={tool.tool_id} className="hover:bg-muted/50">
                        <TableCell className="font-medium">
                          <Link href={`/dashboard/tools/${tool.tool_id}`} className="hover:underline">
                            {tool.name}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <code className="text-xs font-mono bg-muted px-1 py-0.5 rounded">{tool.tool_id}</code>
                        </TableCell>
                        <TableCell className="max-w-[300px] truncate">{tool.description || "No description"}</TableCell>
                        <TableCell>
                          {tool.category ? (
                            <ResourceBadge 
                              subtype={tool.category.toLowerCase() === "api" ? "api" : 
                                      tool.category.toLowerCase().includes("code") ? "code" : 
                                      tool.category.toLowerCase().includes("data") ? "database" : 
                                      tool.category.toLowerCase().includes("web") ? "web" : "document"}
                            >
                              {tool.category}
                            </ResourceBadge>
                          ) : (
                            <span className="text-muted-foreground">Uncategorized</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {tool.permissions_required && tool.permissions_required.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {tool.permissions_required.map(permId => {
                                const scopeName = scopeMap.get(permId) || 'Unknown';
                                const badgeSubtype = getScopeBadgeSubtype(scopeName);
                                return (
                                  <ScopeBadge key={permId} subtype={badgeSubtype} title={scopeName}>
                                    {scopeName} {/* Display scope name inside badge */}
                                  </ScopeBadge>
                                );
                              })}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">None</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <StatusBadge 
                            subtype={tool.is_active ? "success" : "inactive"}
                          >
                            {tool.is_active ? "Active" : "Inactive"}
                          </StatusBadge>
                        </TableCell>
                        <TableCell>
                          {tool.created_at ? (
                            <span title={new Date(tool.created_at).toLocaleString()}>
                              {formatTimeAgo(tool.created_at)}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">Unknown</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <ToolActions tool={tool} onUpdate={fetchTools} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {activeFilter !== 'all' && filteredTools.length === 0 && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-md text-center">
                    <p className="text-muted-foreground">No {activeFilter} tools found. Try a different filter.</p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No tools registered yet. Click "Register New Tool" to create one.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
