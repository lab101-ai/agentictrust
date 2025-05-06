"use client";

import { Agent } from "@/lib/api";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { SecurityBadge, ResourceBadge, IconBadge } from "@/components/ui/icon-badge";

interface AgentPermissionsCardProps {
  agent: Agent;
  isLoading?: boolean;
}

export const AgentPermissionsCard = ({ agent, isLoading = false }: AgentPermissionsCardProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Tools & Resources</CardTitle>
        <CardDescription>
          Permissions and resources granted to this agent
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div>
            <p className="font-medium mb-2">Authorized Tools:</p>
            <div className="flex flex-wrap gap-1">
              {agent.tool_ids && agent.tool_ids.length > 0 ? 
                agent.tool_ids.map((tool: string, idx: number) => (
                  <IconBadge key={idx} variant="secondary">{tool}</IconBadge>
                )) 
                : <span className="text-muted-foreground">None</span>
              }
            </div>
          </div>
          
          <div>
            <p className="font-medium mb-2">Allowed Resources:</p>
            <div className="flex flex-wrap gap-1">
              {agent.allowed_resources && agent.allowed_resources.length > 0 ? 
                agent.allowed_resources.map((resource: string, idx: number) => (
                  <ResourceBadge key={idx} subtype="external">{resource}</ResourceBadge>
                )) 
                : <span className="text-muted-foreground">None</span>
              }
            </div>
          </div>
          
          <div>
            <p className="font-medium mb-2">Security Level:</p>
            <div className="flex flex-wrap gap-1">
              {agent.max_scope_level === "elevated" ? (
                <SecurityBadge subtype="elevated">Elevated Access</SecurityBadge>
              ) : agent.max_scope_level === "standard" ? (
                <SecurityBadge subtype="standard">Standard Access</SecurityBadge>
              ) : (
                <SecurityBadge subtype="restricted">Restricted Access</SecurityBadge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
