"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { IconBadge, StatusBadge, ResourceBadge, TimeBadge, PolicyBadge } from "@/components/ui/icon-badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PolicyAPI, AuditAPI, type Policy, type AuditLog } from "@/lib/api";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  BarChart3, 
  TrendingUp, 
  ShieldAlert, 
  ShieldCheck, 
  Shield, 
  Clock, 
  Users,
  AlertCircle
} from "lucide-react";

// Define the metrics structure for type safety
interface PolicyMetrics {
  evaluations: {
    total: number;
    allowed: number;
    denied: number;
    byDay: number[];
  };
  policies: {
    total: number;
    active: number;
    allow: number;
    deny: number;
  };
  topDenied: Array<{name: string; count: number}>;
  topAllowed: Array<{name: string; count: number}>;
}

export default function PolicyMetricsPage() {
  const [metrics, setMetrics] = useState<PolicyMetrics | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // No longer using tabs
  const router = useRouter();

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Load policies, audit logs, and metrics data in parallel
        const [policiesData, auditLogsData, metricsData] = await Promise.all([
          PolicyAPI.getAll(),
          AuditAPI.search({ event_type: "policy_evaluation", limit: 100 }),
          PolicyAPI.getMetrics()
        ]);
        
        setPolicies(policiesData);
        setAuditLogs(auditLogsData);
        setMetrics(metricsData);
        
      } catch (error) {
        setError(`Failed to load metrics: ${(error as Error).message}`);
        toast.error(`Failed to load metrics: ${(error as Error).message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Calculate the percentage ratio for the metrics
  const getAllowedPercentage = () => {
    if (!metrics) return 0;
    const { allowed, total } = metrics.evaluations;
    return total > 0 ? Math.round((allowed / total) * 100) : 0;
  };

  const getDeniedPercentage = () => {
    if (!metrics) return 0;
    const { denied, total } = metrics.evaluations;
    return total > 0 ? Math.round((denied / total) * 100) : 0;
  };

  const getPolicyTypePercentage = (type: 'allow' | 'deny') => {
    if (!metrics) return 0;
    const { total } = metrics.policies;
    const count = metrics.policies[type];
    return total > 0 ? Math.round((count / total) * 100) : 0;
  };

  if (isLoading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Skeleton className="h-10 w-10 rounded-full mr-4" />
          <Skeleton className="h-10 w-[300px]" />
        </div>

        <div className="grid gap-6">
          <Skeleton className="h-[400px] w-full" />
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-[200px] w-full" />
            <Skeleton className="h-[200px] w-full" />
            <Skeleton className="h-[200px] w-full" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-6">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => router.back()} className="mr-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-semibold">Policy Metrics & Analytics</h1>
      </div>

      <div className="space-y-6">
        {/* Overview section */}
        <div className="flex items-center mb-2">
          <BarChart3 className="mr-2 h-5 w-5" />
          <h2 className="text-xl font-semibold">Overview</h2>
        </div>
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <PolicyBadge subtype="allow">
                    Total Evaluations
                  </PolicyBadge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.evaluations.total.toLocaleString() || '0'}</div>
                <p className="text-xs text-muted-foreground">
                  Policy evaluation requests
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <IconBadge icon={ShieldCheck} variant="default" />
                  Access Allowed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.evaluations.allowed.toLocaleString() || '0'}</div>
                <p className="text-xs text-muted-foreground">
                  {getAllowedPercentage()}% of total evaluations
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <IconBadge icon={ShieldAlert} variant="destructive" />
                  Access Denied
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.evaluations.denied.toLocaleString() || '0'}</div>
                <p className="text-xs text-muted-foreground">
                  {getDeniedPercentage()}% of total evaluations
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <PolicyBadge subtype="active">
                    Active Policies
                  </PolicyBadge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics ? `${metrics.policies.active} / ${metrics.policies.total}` : '0 / 0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {getPolicyTypePercentage('allow')}% allow, {getPolicyTypePercentage('deny')}% deny
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Access Denied Policies</CardTitle>
                <CardDescription>
                  Policies that most frequently deny access
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {metrics?.topDenied.map((policy, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-4 text-lg font-semibold text-muted-foreground">
                          #{i + 1}
                        </div>
                        <div>
                          <div className="font-medium">{policy.name}</div>
                          <PolicyBadge 
                            subtype="deny"
                            className="mt-1"
                          >
                            {policy.count} denials
                          </PolicyBadge>
                        </div>
                      </div>
                      <PolicyBadge subtype="deny" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Access Allowed Policies</CardTitle>
                <CardDescription>
                  Policies that most frequently allow access
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {metrics?.topAllowed.map((policy, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-4 text-lg font-semibold text-muted-foreground">
                          #{i + 1}
                        </div>
                        <div>
                          <div className="font-medium">{policy.name}</div>
                          <PolicyBadge 
                            subtype="allow"
                            className="mt-1"
                          >
                            {policy.count} approvals
                          </PolicyBadge>
                        </div>
                      </div>
                      <PolicyBadge subtype="allow" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        
        {/* Usage Trends section */}
        <div className="flex items-center mb-2 mt-8">
          <TrendingUp className="mr-2 h-5 w-5" />
          <h2 className="text-xl font-semibold">Usage Trends</h2>
        </div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="mr-2 h-4 w-4" />
                Weekly Evaluation Trends
              </CardTitle>
              <CardDescription>
                Policy evaluation activity over the past 7 days
              </CardDescription>
            </CardHeader>
            <CardContent>
              {error ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <StatusBadge 
                      icon={AlertCircle} 
                      variant="destructive" 
                      className="mx-auto mb-4"
                    >
                      Error Loading Data
                    </StatusBadge>
                    <p className="text-sm text-muted-foreground">{error}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4"
                      onClick={() => window.location.reload()}
                    >
                      Retry
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center border rounded-md bg-muted/20">
                  <div className="text-center">
                    <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
                    <p className="mt-2 text-sm text-muted-foreground">
                      Visualization in development. Coming soon!
                    </p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-4"
                      onClick={() => router.push("/dashboard/policies/new")}
                    >
                      Create New Policy
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="mr-2 h-5 w-5" />
                  Agent Access Patterns
                </CardTitle>
                <CardDescription>
                  Common access patterns by agent type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[200px] flex items-center justify-center border rounded-md bg-muted/20">
                  <p className="text-sm text-muted-foreground">
                    Visualization in development
                  </p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="mr-2 h-5 w-5" />
                  Policy Effectiveness
                </CardTitle>
                <CardDescription>
                  Impact of policies on system access
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[200px] flex items-center justify-center border rounded-md bg-muted/20">
                  <p className="text-sm text-muted-foreground">
                    Visualization in development
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
      </div>
    </div>
  );
}
