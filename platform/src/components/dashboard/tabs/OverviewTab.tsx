"use client";

import { useEffect, useState } from "react";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Users, Wrench, Key, Shield, History, BarChart } from "lucide-react";
import { DashboardStats, StatsAPI, AuditAPI, AuditLog, ScopeAPI, Scope } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";

export function OverviewTab() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [sensitiveScopes, setSensitiveScopes] = useState<Scope[]>([]);
  const [loading, setLoading] = useState({
    stats: false,
    logs: false,
    scopes: false
  });
  const [error, setError] = useState({
    stats: false,
    logs: false,
    scopes: false
  });

  // Fetch stats
  const fetchStats = async () => {
    setLoading(prev => ({ ...prev, stats: true }));
    setError(prev => ({ ...prev, stats: false }));
    try {
      const data = await StatsAPI.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(prev => ({ ...prev, stats: true }));
      toast.error("Failed to load dashboard statistics");
    } finally {
      setLoading(prev => ({ ...prev, stats: false }));
    }
  };

  // Fetch recent logs
  const fetchRecentLogs = async () => {
    setLoading(prev => ({ ...prev, logs: true }));
    setError(prev => ({ ...prev, logs: false }));
    try {
      const data = await AuditAPI.getAll(5); // Get just the 5 most recent logs
      setRecentLogs(data);
    } catch (err) {
      setError(prev => ({ ...prev, logs: true }));
      toast.error("Failed to load recent activity");
    } finally {
      setLoading(prev => ({ ...prev, logs: false }));
    }
  };

  // Fetch sensitive scopes
  const fetchSensitiveScopes = async () => {
    setLoading(prev => ({ ...prev, scopes: true }));
    setError(prev => ({ ...prev, scopes: false }));
    try {
      const allScopes = await ScopeAPI.getAll();
      const sensitive = allScopes.filter(scope => scope.is_sensitive === true);
      setSensitiveScopes(sensitive);
    } catch (err) {
      setError(prev => ({ ...prev, scopes: true }));
      toast.error("Failed to load scope information");
    } finally {
      setLoading(prev => ({ ...prev, scopes: false }));
    }
  };

  // Function to format event types for display
  const formatEventType = (eventType: string): string => {
    return eventType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  useEffect(() => {
    fetchStats();
    fetchRecentLogs();
    fetchSensitiveScopes();

    // Set up refresh listener
    const handleRefresh = () => {
      fetchStats();
      fetchRecentLogs();
      fetchSensitiveScopes();
    };

    window.addEventListener('dashboard:refresh', handleRefresh);
    return () => window.removeEventListener('dashboard:refresh', handleRefresh);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Registered Agents"
          value={loading.stats ? undefined : stats?.agents_count}
          description="Total agents in the system"
          icon={<Users className="h-5 w-5" />}
          trend="+2 this month"
        />
        <StatsCard
          title="Available Tools"
          value={loading.stats ? undefined : stats?.tools_count}
          description="Tools ready for agent use"
          icon={<Wrench className="h-5 w-5" />}
          trend="+5 this month"
        />
        <StatsCard
          title="Active Tokens"
          value={loading.stats ? undefined : stats?.active_tokens_count}
          description="Currently valid OAuth tokens"
          icon={<Key className="h-5 w-5" />}
          trend="+12 this week"
        />
        <StatsCard
          title="Total Tokens"
          value={loading.stats ? undefined : stats?.tokens_count}
          description="All time token count"
          icon={<BarChart className="h-5 w-5" />}
          trend="+23% from last month"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart className="h-5 w-5" />
              Platform Status
            </CardTitle>
            <CardDescription>Current system health and performance</CardDescription>
          </CardHeader>
          <CardContent>
            {error.stats ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading status</AlertTitle>
                <AlertDescription>Unable to fetch platform status.</AlertDescription>
              </Alert>
            ) : loading.stats ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm font-medium">Service Status</span>
                  <span className="text-sm">Last updated: {new Date().toLocaleTimeString()}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">API Services</span>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Authentication</span>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Tool Integration</span>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Scope Management</span>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Audit Logging</span>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Recent Activity
            </CardTitle>
            <CardDescription>Latest actions across the platform</CardDescription>
          </CardHeader>
          <CardContent>
            {error.logs ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading activity</AlertTitle>
                <AlertDescription>Unable to fetch recent activities.</AlertDescription>
              </Alert>
            ) : loading.logs ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : (
              <div className="space-y-4">
                {recentLogs.length > 0 ? (
                  <div className="space-y-2">
                    {recentLogs.map((log) => (
                      <div key={log.log_id} className="flex justify-between items-center border-b pb-2">
                        <div>
                          <div className="text-sm font-medium">{formatEventType(log.event_type)}</div>
                          <div className="text-xs text-muted-foreground">
                            Client: {log.client_id.substring(0, 8)}...
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge 
                            variant={
                              log.status === "success" ? "default" : 
                              log.status === "failed" ? "destructive" : 
                              "secondary"
                            }
                            className="text-xs"
                          >
                            {log.status}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground">No recent activity</div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security & Permissions
            </CardTitle>
            <CardDescription>Sensitive scopes and permission insights</CardDescription>
          </CardHeader>
          <CardContent>
            {error.scopes ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading scope data</AlertTitle>
                <AlertDescription>Unable to fetch sensitive scopes.</AlertDescription>
              </Alert>
            ) : loading.scopes ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-20 w-full" />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="border-b pb-2">
                  <h4 className="text-sm font-medium">Sensitive Scopes</h4>
                  <p className="text-xs text-muted-foreground">Scopes that require special handling</p>
                </div>
                
                {sensitiveScopes.length > 0 ? (
                  <div className="space-y-2">
                    {sensitiveScopes.map((scope) => (
                      <div key={scope.scope_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="destructive" className="text-xs">Sensitive</Badge>
                          <span className="text-sm font-medium">{scope.name}</span>
                        </div>
                        <div>
                          <Badge variant="outline" className="text-xs">{scope.category}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground">No sensitive scopes defined</div>
                )}
                
                <div className="border-t pt-4 mt-4">
                  <h4 className="text-sm font-medium mb-2">Security Metrics</h4>
                  
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Token Security</span>
                        <span className="text-sm font-medium">85%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div className="bg-green-600 h-2.5 rounded-full" style={{ width: '85%' }}></div>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Scope Coverage</span>
                        <span className="text-sm font-medium">72%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: '72%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
