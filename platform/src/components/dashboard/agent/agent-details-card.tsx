"use client";

import { Agent } from "@/lib/api";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { StatusBadge, SecurityBadge, ResourceBadge, IconBadge } from "@/components/ui/icon-badge";

interface AgentDetailsCardProps {
  agent: Agent;
  isLoading?: boolean;
}

export const AgentDetailsCard = ({ agent, isLoading = false }: AgentDetailsCardProps) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle>Agent Details</CardTitle>
          <CardDescription>
            Basic information about this agent
          </CardDescription>
        </div>
        <div>
          {agent.is_active ? (
            <StatusBadge subtype="success">Active</StatusBadge>
          ) : (
            <StatusBadge subtype="inactive">Inactive</StatusBadge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-4 items-start gap-3">
          <p className="font-medium text-right text-muted-foreground">ID:</p>
          <p className="col-span-3 font-mono text-sm break-all">{agent.client_id}</p>
          
          <p className="font-medium text-right text-muted-foreground">Name:</p>
          <p className="col-span-3">{agent.agent_name}</p>
          
          <p className="font-medium text-right text-muted-foreground">Description:</p>
          <p className="col-span-3">{agent.description || 'No description provided'}</p>
          
          <p className="font-medium text-right text-muted-foreground">Created At:</p>
          <p className="col-span-3">{agent.created_at ? new Date(agent.created_at).toLocaleString() : 'N/A'}</p>
          
          <p className="font-medium text-right text-muted-foreground">Updated At:</p>
          <p className="col-span-3">{agent.updated_at ? new Date(agent.updated_at).toLocaleString() : 'N/A'}</p>
          
          <p className="font-medium text-right text-muted-foreground">Max Scope Level:</p>
          <div className="col-span-3">
            {agent.max_scope_level === "elevated" ? (
              <SecurityBadge subtype="elevated">Elevated</SecurityBadge>
            ) : agent.max_scope_level === "standard" ? (
              <SecurityBadge subtype="standard">Standard</SecurityBadge>
            ) : (
              <SecurityBadge subtype="restricted">Restricted</SecurityBadge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
