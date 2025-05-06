"use client";

import { useState, useEffect, useMemo } from "react";
import { AgentAPI, Agent } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { IconBadge, StatusBadge, SecurityBadge } from "@/components/ui/icon-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { AlertCircle, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

import AgentActions from "@/components/dashboard/AgentActions";

import { formatTimeAgo } from "@/lib/utils";

export function AgentsTab() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const router = useRouter();

  const fetchAgents = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await AgentAPI.getAll();
      setAgents(data);
      applyFilter(activeFilter, data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load agents");
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = (filter: 'all' | 'active' | 'inactive', agentData = agents) => {
    setActiveFilter(filter);
    switch (filter) {
      case 'active':
        setFilteredAgents(agentData.filter(agent => agent.is_active));
        break;
      case 'inactive':
        setFilteredAgents(agentData.filter(agent => !agent.is_active));
        break;
      default:
        setFilteredAgents(agentData);
    }
  };

  useEffect(() => {
    fetchAgents();

    // Set up refresh listener
    const handleRefresh = () => {
      fetchAgents();
    };

    window.addEventListener('dashboard:refresh', handleRefresh);
    return () => window.removeEventListener('dashboard:refresh', handleRefresh);
  }, []);

  return (
    <Card id="agents">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Agents</CardTitle>
            <CardDescription>View and manage AI agents</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={() => router.push('/dashboard/agents/new')} 
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Agent
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading agents</AlertTitle>
            <AlertDescription>There was a problem fetching the agent data.</AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`agent-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            {agents.length > 0 ? (
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
                      <TableHead>Client ID</TableHead>
                      <TableHead>Max Scope</TableHead>
                      <TableHead>Tool Count</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredAgents.map((agent) => (
                      <TableRow key={agent.client_id} className="hover:bg-muted/50">
                        <TableCell className="font-medium">
                          <Link href={`/dashboard/agents/${agent.client_id}`} className="hover:underline">
                            {agent.agent_name}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <code className="text-xs font-mono bg-muted px-1 py-0.5 rounded">{agent.client_id.substring(0, 8)}...</code>
                        </TableCell>
                        <TableCell>
                          {agent.max_scope_level ? (
                            <SecurityBadge subtype={agent.max_scope_level as 'restricted' | 'standard' | 'elevated'}> 
                              {agent.max_scope_level}
                            </SecurityBadge>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {(agent.tool_ids?.length ?? agent.tools?.length ?? 0)}
                        </TableCell>
                        <TableCell>
                          <StatusBadge subtype={agent.is_active ? "success" : "inactive"}>
                            {agent.is_active ? "Active" : "Inactive"}
                          </StatusBadge>
                        </TableCell>
                        <TableCell>
                          <span title={new Date(agent.created_at).toLocaleString()}>{formatTimeAgo(agent.created_at)}</span>
                        </TableCell>
                        <TableCell>
                          <AgentActions agent={agent} onUpdate={fetchAgents} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {activeFilter !== 'all' && filteredAgents.length === 0 && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-md text-center">
                    <p className="text-muted-foreground">No {activeFilter} agents found. Try a different filter.</p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No agents available yet. Click "New Agent" to create one.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
