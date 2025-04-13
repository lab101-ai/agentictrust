"use client";

import { StatsCard } from "@/components/dashboard/StatsCard";
import { RegisterAgentDialog } from "@/components/dashboard/RegisterAgentDialog";
import { RegisterToolDialog } from "@/components/dashboard/RegisterToolDialog";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Agent, AgentAPI, Tool, ToolAPI, Token, TokenAPI, AuditLog, AuditAPI, StatsAPI, DashboardStats, Scope, ScopeAPI } from "@/lib/api";
import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import ToolActions from "@/components/dashboard/ToolActions";
import AgentActions from "@/components/dashboard/AgentActions";
import TokenActions from "@/components/dashboard/TokenActions";
import LogActions from "@/components/dashboard/LogActions";
import ScopeActions from "@/components/dashboard/ScopeActions";
import { RegisterScopeDialog } from "@/components/dashboard/RegisterScopeDialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSearchParams, useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Helper function to format event types for display
function formatEventType(eventType: string): string {
  return eventType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Function to get event class based on event type
function getEventClass(event: string): string {
  if (event.includes('token')) {
    return 'bg-blue-100 text-blue-800';
  } else if (event.includes('agent')) {
    return 'bg-green-100 text-green-800';
  } else if (event.includes('tool')) {
    return 'bg-purple-100 text-purple-800';
  } else {
    return 'bg-gray-100 text-gray-800';
  }
}

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const currentTab = searchParams.get('tab') || 'overview';
  
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    agents_count: 0,
    tools_count: 0,
    tokens_count: 0,
    active_tokens_count: 0
  });

  // Define the Scope interface based on the API structure
  interface Scope {
    scope_id: string;
    name: string;
    description: string;
    category: string;
    is_default?: boolean;
    is_sensitive?: boolean;
    requires_approval?: boolean;
    is_active?: boolean;
    created_at?: string;
    updated_at?: string;
  }
  
  const [scopes, setScopes] = useState<Scope[]>([]);
  
  // Track loading and error states for each data type
  const [loading, setLoading] = useState({
    agents: true,
    tools: true,
    tokens: true,
    logs: true,
    stats: true,
    scopes: true
  });
  
  const [error, setError] = useState({
    agents: false,
    tools: false,
    tokens: false,
    logs: false,
    stats: false,
    scopes: false
  });
  
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Function to handle tab changes
  const handleTabChange = (value: string) => {
    router.push(`/dashboard?tab=${value}`);
  };
  
  // Function to refresh data
  const refreshData = useCallback(async () => {
    setIsRefreshing(true);
    await fetchAllData();
    setIsRefreshing(false);
    toast.success("Dashboard data refreshed");
  }, []);
  
  // Fetch individual data types separately to handle errors gracefully
  const fetchAgents = async () => {
    setLoading((prev) => ({ ...prev, agents: true }));
    setError((prev) => ({ ...prev, agents: false }));
    try {
      const data = await AgentAPI.getAll();
      setAgents(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, agents: true }));
      toast.error("Failed to load agents");
    } finally {
      setLoading((prev) => ({ ...prev, agents: false }));
    }
  };
  
  const fetchTools = async () => {
    setLoading((prev) => ({ ...prev, tools: true }));
    setError((prev) => ({ ...prev, tools: false }));
    try {
      const data = await ToolAPI.getAll();
      setTools(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, tools: true }));
      toast.error("Failed to load tools");
    } finally {
      setLoading((prev) => ({ ...prev, tools: false }));
    }
  };
  
  const fetchTokens = async () => {
    setLoading((prev) => ({ ...prev, tokens: true }));
    setError((prev) => ({ ...prev, tokens: false }));
    try {
      const data = await TokenAPI.getAll();
      setTokens(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, tokens: true }));
      toast.error("Failed to load tokens");
    } finally {
      setLoading((prev) => ({ ...prev, tokens: false }));
    }
  };
  
  const fetchLogs = async () => {
    setLoading((prev) => ({ ...prev, logs: true }));
    setError((prev) => ({ ...prev, logs: false }));
    try {
      const data = await AuditAPI.getAll(10);
      setLogs(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, logs: true }));
      toast.error("Failed to load audit logs");
    } finally {
      setLoading((prev) => ({ ...prev, logs: false }));
    }
  };
  
  const fetchStats = async () => {
    setLoading((prev) => ({ ...prev, stats: true }));
    setError((prev) => ({ ...prev, stats: false }));
    try {
      const data = await StatsAPI.getDashboardStats();
      setStats(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, stats: true }));
      toast.error("Failed to load dashboard statistics");
    } finally {
      setLoading((prev) => ({ ...prev, stats: false }));
    }
  };
  
  // Fetch scopes data
  const fetchScopes = async () => {
    setLoading((prev) => ({ ...prev, scopes: true }));
    setError((prev) => ({ ...prev, scopes: false }));
    try {
      // Use the ScopeAPI class that follows the same pattern as other APIs
      const data = await ScopeAPI.getAll();
      setScopes(data);
    } catch (err) {
      // Error handled by toast and state
      setError((prev) => ({ ...prev, scopes: true }));
      toast.error("Failed to load scopes");
    } finally {
      setLoading((prev) => ({ ...prev, scopes: false }));
    }
  };

  // Combined function to fetch all data
  const fetchAllData = async () => {
    await Promise.all([
      fetchAgents(),
      fetchTools(),
      fetchTokens(),
      fetchLogs(),
      fetchStats(),
      fetchScopes()
    ]);
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchAllData();
    // Set up auto-refresh every 30 seconds
    const refreshInterval = setInterval(() => {
      fetchAllData();
    }, 30000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  const isLoading = Object.values(loading).some(val => val === true);
  
  // Function to render loading skeletons
  const renderSkeletons = (count: number) => {
    return Array(count)
      .fill(0)
      .map((_, i) => (
        <tr key={`skeleton-${i}`}>
          <td colSpan={6} className="p-2">
            <Skeleton className="h-12 w-full" />
          </td>
        </tr>
      ));
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <Button 
          onClick={refreshData} 
          variant="outline" 
          size="sm"
          disabled={isRefreshing}
          className="gap-2"
        >
          <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard value={loading.stats ? '...' : stats.agents_count} label="Registered Agents" />
        <StatsCard value={loading.stats ? '...' : stats.tools_count} label="Registered Tools" />
        <StatsCard value={loading.stats ? '...' : stats.tokens_count} label="Total Tokens" />
        <StatsCard value={loading.stats ? '...' : stats.active_tokens_count} label="Active Tokens" />
      </div>
      
      <Tabs value={currentTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid grid-cols-6 mb-8">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="tokens">Tokens</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
          <TabsTrigger value="scopes">Scopes</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Current system status and metrics</CardDescription>
              </CardHeader>
              <CardContent>
                {error.stats ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error loading system stats</AlertTitle>
                    <AlertDescription>There was a problem fetching the system health data.</AlertDescription>
                  </Alert>
                ) : loading.stats ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-4 w-5/6" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-sm font-medium">Active agents</span>
                      <span className="font-bold">{agents.filter(a => a.is_active).length} / {agents.length}</span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-sm font-medium">Active tools</span>
                      <span className="font-bold">{tools.filter(t => t.is_active).length} / {tools.length}</span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b">
                      <span className="text-sm font-medium">Token usage</span>
                      <span className="font-bold">{stats.active_tokens_count} / {stats.tokens_count}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest system events</CardDescription>
              </CardHeader>
              <CardContent>
                {error.logs ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error loading activity</AlertTitle>
                    <AlertDescription>There was a problem fetching the recent activity.</AlertDescription>
                  </Alert>
                ) : loading.logs ? (
                  <div className="space-y-2">
                    {Array(3).fill(0).map((_, i) => (
                      <Skeleton key={`activity-skeleton-${i}`} className="h-10 w-full" />
                    ))}
                  </div>
                ) : logs.length === 0 ? (
                  <div className="text-center py-4 text-muted-foreground">
                    No recent activity recorded
                  </div>
                ) : (
                  <div className="space-y-3">
                    {logs.slice(0, 5).map((log) => (
                      <div key={log.log_id} className="flex items-start gap-2 text-sm border-b pb-2">
                        <div className={`rounded-full px-2 py-1 text-xs ${getEventClass(log.event_type)}`}>
                          {log.event_type.split('_')[0]}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium">{formatEventType(log.event_type)}</div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Badge variant={log.status === 'success' ? 'default' : 'secondary'}>
                          {log.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
              <CardFooter className="flex justify-center">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleTabChange('audit')}
                  className="w-full"
                >
                  View all activity
                </Button>
              </CardFooter>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="agents">
          <Card id="agents">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Agents</CardTitle>
                <CardDescription>Manage registered AI agents and their permissions</CardDescription>
              </div>
              <RegisterAgentDialog />
            </CardHeader>
            <CardContent>
              {agents.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Client ID</TableHead>
                      <TableHead>Agent Name</TableHead>
                      <TableHead>Max Scope Level</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Tools</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agents.map((agent) => (
                      <TableRow key={agent.client_id}>
                        <TableCell className="font-mono text-xs">{agent.client_id}</TableCell>
                        <TableCell>{agent.agent_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{agent.max_scope_level || 'restricted'}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={agent.is_active ? "default" : "secondary"}>
                            {agent.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell>{agent.tools?.length || 0} tools</TableCell>
                        <TableCell>
                          <AgentActions agent={agent} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="bg-muted p-4 rounded-md text-center">
                  No agents registered yet. Click "Register New Agent" to create one.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="tools">
          <Card id="tools">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Tools</CardTitle>
                <CardDescription>Manage tools that agents can access</CardDescription>
              </div>
              <RegisterToolDialog />
            </CardHeader>
            <CardContent>
              {tools.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tool ID</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tools.map((tool) => (
                      <TableRow key={tool.tool_id}>
                        <TableCell className="font-mono text-xs">{tool.tool_id}</TableCell>
                        <TableCell>{tool.name}</TableCell>
                        <TableCell>{tool.category || 'N/A'}</TableCell>
                        <TableCell>
                          <Badge variant={tool.is_active ? "default" : "secondary"}>
                            {tool.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {tool.permissions_required && tool.permissions_required.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {tool.permissions_required.map((perm, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {perm}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">None</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <ToolActions tool={tool} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="bg-muted p-4 rounded-md text-center">
                  No tools registered yet. Click "Register New Tool" to create one.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="tokens">
          <Card id="tokens">
            <CardHeader>
              <CardTitle>Token Management</CardTitle>
              <CardDescription>View and manage OAuth tokens with their task inheritance</CardDescription>
            </CardHeader>
            <CardContent>
              {tokens.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Token ID</TableHead>
                      <TableHead>Client ID</TableHead>
                      <TableHead>Task ID</TableHead>
                      <TableHead>Parent Task</TableHead>
                      <TableHead>Scope Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tokens.map((token) => (
                      <TableRow key={token.token_id}>
                        <TableCell className="font-mono text-xs">{token.token_id}</TableCell>
                        <TableCell className="font-mono text-xs">{token.client_id}</TableCell>
                        <TableCell className="font-mono text-xs">{token.task_id || 'N/A'}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {token.parent_task_id ? (
                            <Badge variant="outline" className="text-xs">
                              {token.parent_task_id.substring(0, 8)}...
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">Root</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{token.scope_inheritance_type || 'restricted'}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={
                              token.is_revoked ? "destructive" : 
                              new Date(token.expires_at) < new Date() ? "secondary" : 
                              "default"
                            }
                          >
                            {token.is_revoked ? "Revoked" : 
                             new Date(token.expires_at) < new Date() ? "Expired" : 
                             "Active"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <TokenActions token={token} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="bg-muted p-4 rounded-md text-center">
                  No active tokens available.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="scopes">
          <Card id="scopes">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>OAuth Scopes</CardTitle>
                <CardDescription>Manage available scopes and their permissions</CardDescription>
              </div>
              <RegisterScopeDialog onScopeAdded={fetchScopes} />
            </CardHeader>
            <CardContent>
              {error.scopes ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error loading scopes</AlertTitle>
                  <AlertDescription>There was a problem fetching the scopes data.</AlertDescription>
                </Alert>
              ) : loading.scopes ? (
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
        </TabsContent>
        
        <TabsContent value="audit">
            <Card id="audit-logs">
              <CardHeader>
                <CardTitle>Audit Logs</CardTitle>
                <CardDescription>View system activity and security events</CardDescription>
              </CardHeader>
              <CardContent>
              {logs.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Task ID</TableHead>
                      <TableHead>Parent Task</TableHead>
                      <TableHead>Event Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.log_id}>
                        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs">{log.client_id.substring(0, 8)}...</TableCell>
                        <TableCell className="font-mono text-xs">
                          {log.task_id ? log.task_id.substring(0, 8) + '...' : 'N/A'}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {log.parent_task_id ? log.parent_task_id.substring(0, 8) + '...' : 'N/A'}
                        </TableCell>
                        <TableCell>{log.event_type}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={
                              log.status === "success" ? "default" : 
                              log.status === "failed" ? "destructive" : 
                              "secondary"
                            }
                          >
                            {log.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <LogActions log={log} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="bg-muted p-4 rounded-md text-center">
                  No audit logs available yet.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 