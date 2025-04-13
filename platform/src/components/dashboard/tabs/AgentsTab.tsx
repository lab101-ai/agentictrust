"use client";

import { useState, useEffect } from "react";
import { Agent, AgentAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Users, Calendar, Info, Check, X } from "lucide-react";
import { RegisterAgentDialog } from "@/components/dashboard/RegisterAgentDialog";
import AgentActions from "@/components/dashboard/AgentActions";
import { Button } from "@/components/ui/button";

export function AgentsTab() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

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
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          <div>
            <CardTitle>Registered Agents</CardTitle>
            <CardDescription>View and manage AI agents</CardDescription>
          </div>
        </div>
        <RegisterAgentDialog onAgentAdded={fetchAgents} />
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
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAgents.map((agent) => (
                    <TableRow key={agent.client_id}>
                      <TableCell className="font-medium">{agent.agent_name}</TableCell>
                      <TableCell className="font-mono text-xs">{agent.client_id.substring(0, 8)}...</TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        <div className="flex items-center gap-1">
                          <Info className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>{agent.description || "No description"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={agent.is_active ? "default" : "secondary"}>
                          {agent.is_active ? (
                            <div className="flex items-center gap-1">
                              <Check className="h-3 w-3" /> Active
                            </div>
                          ) : (
                            <div className="flex items-center gap-1">
                              <X className="h-3 w-3" /> Inactive
                            </div>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>{new Date(agent.created_at).toLocaleDateString()}</span>
                        </div>
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
                No agents registered yet. Click "Register New Agent" to create one.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
