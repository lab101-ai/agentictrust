"use client";

import { useEffect, useState } from "react";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Bot, Users, Wrench, Key, FileCode, History, BarChart, Globe } from "lucide-react";
import { DashboardStats, StatsAPI, AuditAPI, AuditLog, ScopeAPI, Scope, DiscoveryAPI, OIDCConfiguration, JWKS } from "@/lib/api";
import { toast } from "sonner";
// Badge import removed in favor of IconBadge components
import { StatusBadge } from "@/components/ui/icon-badge";

export function OverviewTab() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [sensitiveScopes, setSensitiveScopes] = useState<Scope[]>([]);
  const [currentTime, setCurrentTime] = useState<string>("");
  const [discoveryConfig, setDiscoveryConfig] = useState<OIDCConfiguration | null>(null);
  const [jwks, setJwks] = useState<JWKS | null>(null);
  const [loading, setLoading] = useState({
    stats: false,
    logs: false,
    scopes: false,
    policies: false,
    discovery: false
  });
  const [error, setError] = useState({
    stats: false,
    logs: false,
    scopes: false,
    policies: false,
    discovery: false
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

  // Fetch discovery endpoints
  const fetchDiscoveryData = async () => {
    setLoading(prev => ({ ...prev, discovery: true }));
    setError(prev => ({ ...prev, discovery: false }));
    try {
      // Fetch OpenID Configuration
      const configData = await DiscoveryAPI.getOIDCConfiguration();
      setDiscoveryConfig(configData);
      
      // Fetch JWKS
      const jwksData = await DiscoveryAPI.getJWKS();
      setJwks(jwksData);
    } catch (err) {
      setError(prev => ({ ...prev, discovery: true }));
      console.error("Failed to fetch discovery endpoints:", err);
      // No toast for this to avoid overwhelming the user
    } finally {
      setLoading(prev => ({ ...prev, discovery: false }));
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
    fetchDiscoveryData();
    
    // Initialize the current time for client-side only
    setCurrentTime(new Date().toLocaleTimeString());
    
    // Update time every minute
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 60000);

    // Set up refresh listener
    const handleRefresh = () => {
      fetchStats();
      fetchRecentLogs();
      fetchSensitiveScopes();
      fetchDiscoveryData();
      setCurrentTime(new Date().toLocaleTimeString());
    };

    window.addEventListener('dashboard:refresh', handleRefresh);
    return () => {
      window.removeEventListener('dashboard:refresh', handleRefresh);
      clearInterval(timeInterval);
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Agents"
          value={loading.stats ? undefined : stats?.agents_count}
          description="Total agents in the system"
          icon={<Bot className="h-5 w-5" />}
        />
        <StatsCard
          title="Tools"
          value={loading.stats ? undefined : stats?.tools_count}
          description="Tools ready for agent use"
          icon={<Wrench className="h-5 w-5" />}
        />
        <StatsCard
          title="Tokens"
          value={loading.stats ? undefined : stats?.active_tokens_count}
          description="Currently valid OAuth tokens"
          icon={<Key className="h-5 w-5" />}
        />
        <StatsCard
          title="Policies"
          value={loading.stats ? undefined : stats?.policies_count}
          description="Active access policies"
          icon={<FileCode className="h-5 w-5" />}
        />
        <StatsCard
          title="Users"
          value={loading.stats ? undefined : stats?.users_count}
          description="Total platform users"
          icon={<Users className="h-5 w-5" />}
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
                  <span className="text-sm">Last updated: {currentTime}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">API Services</span>
                  <StatusBadge subtype="success" colorClassName="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </StatusBadge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Authentication</span>
                  <StatusBadge subtype="success" colorClassName="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </StatusBadge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Tool Integration</span>
                  <StatusBadge subtype="success" colorClassName="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </StatusBadge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Audit Logging</span>
                  <StatusBadge subtype="success" colorClassName="bg-green-50 text-green-700 border-green-200">
                    Operational
                  </StatusBadge>
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
                        <StatusBadge 
                          subtype={log.status === "success" ? "success" : 
                                  log.status === "failed" ? "error" : 
                                  "info"}
                          className="text-xs"
                        />

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

      {/* Discovery Endpoints */}
      <Card className="md:col-span-3 lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            API Discovery
          </CardTitle>
          <CardDescription>OpenID Connect discovery endpoints</CardDescription>
        </CardHeader>
        <CardContent>
          {error.discovery ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error loading discovery endpoints</AlertTitle>
              <AlertDescription>Unable to fetch OpenID Connect discovery information.</AlertDescription>
            </Alert>
          ) : loading.discovery ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm font-medium">Discovery Endpoints</span>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <div className="text-sm font-medium">OpenID Configuration</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      <a 
                        href="/api/discovery?endpoint=.well-known/openid-configuration" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="truncate text-blue-600 hover:underline inline-block max-w-full"
                      >
                        {`/.well-known/openid-configuration`}
                      </a>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-medium">JSON Web Key Set</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      <a 
                        href="/api/discovery?endpoint=.well-known/jwks.json" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="truncate text-blue-600 hover:underline inline-block max-w-full"
                      >
                        {`/.well-known/jwks.json`}
                      </a>
                    </div>
                  </div>
                </div>

                {discoveryConfig && (
                  <>
                    <div className="mt-4 pt-2 border-t text-sm font-medium">
                      Supported Capabilities
                    </div>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                      <div>
                        <div className="text-xs font-medium">Response Types</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {discoveryConfig.response_types_supported.map(type => (
                            <span key={type} className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100">
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-medium">Grant Types</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {discoveryConfig.grant_types_supported.map(type => (
                            <span key={type} className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100">
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  </div>
);
}
