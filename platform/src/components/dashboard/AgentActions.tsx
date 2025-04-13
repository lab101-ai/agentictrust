"use client";

import { Button } from "@/components/ui/button";
import { Agent, AgentAPI } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { EditAgentDialog } from "./EditAgentDialog";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";

interface AgentActionsProps {
  agent: Agent;
  onUpdate?: () => Promise<void> | void;
}

export default function AgentActions({ agent, onUpdate }: AgentActionsProps) {
  const [isActivating, setIsActivating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const handleActivate = async () => {
    if (!agent.registration_token) {
      toast.error("No registration token available for this agent");
      return;
    }
    
    setIsActivating(true);
    try {
      await AgentAPI.activate(agent.registration_token);
      toast.success(`Agent ${agent.agent_name} activated successfully`);
      // Call the onUpdate callback if provided
      if (onUpdate) {
        await onUpdate();
      }
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to activate agent");
    } finally {
      setIsActivating(false);
    }
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete this agent: ${agent.agent_name}?`)) {
      setIsDeleting(true);
      try {
        await AgentAPI.delete(agent.client_id);
        toast.success(`Agent ${agent.agent_name} deleted successfully`);
        // Call the onUpdate callback if provided
        if (onUpdate) {
          await onUpdate();
        }
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to delete agent");
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <div className="space-x-2">
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => setViewDialogOpen(true)}
      >
        View
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => setEditDialogOpen(true)}
      >
        Edit
      </Button>
      <Button 
        variant="destructive" 
        size="sm"
        onClick={handleDelete}
        disabled={isDeleting}
      >
        {isDeleting ? "Deleting..." : "Delete"}
      </Button>
      
      {!agent.is_active && agent.registration_token && (
        <Button 
          variant="default" 
          size="sm"
          onClick={handleActivate}
          disabled={isActivating}
        >
          {isActivating ? "Activating..." : "Activate"}
        </Button>
      )}
      
      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Agent Details</DialogTitle>
            <DialogDescription>
              Viewing details for agent: {agent.agent_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="mt-4 space-y-6">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Basic Information</h3>
              <div className="grid grid-cols-4 items-start gap-3">
                <p className="font-medium text-right text-muted-foreground">Client ID:</p>
                <p className="col-span-3 font-mono text-sm break-all">{agent.client_id}</p>
                
                <p className="font-medium text-right text-muted-foreground">Name:</p>
                <p className="col-span-3 font-medium">{agent.agent_name}</p>
                
                <p className="font-medium text-right text-muted-foreground">Description:</p>
                <p className="col-span-3">{agent.description || "No description provided"}</p>
                
                <p className="font-medium text-right text-muted-foreground">Status:</p>
                <div className="col-span-3">
                  <Badge variant={agent.is_active ? "default" : "secondary"}>
                    {agent.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                
                <p className="font-medium text-right text-muted-foreground">Created:</p>
                <p className="col-span-3">{new Date(agent.created_at).toLocaleString()}</p>
                
                {agent.updated_at && (
                  <>
                    <p className="font-medium text-right text-muted-foreground">Last Updated:</p>
                    <p className="col-span-3">{new Date(agent.updated_at).toLocaleString()}</p>
                  </>
                )}
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Security & Access Control</h3>
              <div className="grid grid-cols-4 items-start gap-3">
                <p className="font-medium text-right text-muted-foreground">Max Scope Level:</p>
                <div className="col-span-3">
                  <Badge variant="outline">
                    {agent.max_scope_level || "restricted"}
                  </Badge>
                  <p className="text-sm text-muted-foreground mt-1">
                    {agent.max_scope_level === "elevated" 
                      ? "Higher access levels with fewer rate limits and approvals for trusted agents" 
                      : agent.max_scope_level === "standard" 
                      ? "Regular access to common resources with moderate rate limits" 
                      : "Minimal access with strict rate limits and required approvals"}
                  </p>
                </div>
                
                {!agent.is_active && agent.registration_token && (
                  <>
                    <p className="font-medium text-right text-muted-foreground">Registration Token:</p>
                    <div className="col-span-3">
                      <p className="font-mono text-xs break-all bg-muted p-2 rounded-md">
                        {agent.registration_token}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Use this token to activate the agent. It will be invalidated upon activation.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Tools & Resources</h3>
              
              <div className="grid grid-cols-4 items-start gap-3">
                <p className="font-medium text-right text-muted-foreground">Assigned Tools:</p>
                <div className="col-span-3">
                  {agent.tools && agent.tools.length > 0 ? (
                    <div className="space-y-2">
                      {agent.tools.map((tool, index) => (
                        <div key={index} className="border rounded-md p-2">
                          <div className="flex justify-between">
                            <div className="font-medium">{tool.name}</div>
                            <Badge variant={tool.is_active ? "default" : "secondary"} className="ml-2">
                              {tool.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </div>
                          {tool.description && (
                            <p className="text-sm text-muted-foreground mt-1">{tool.description}</p>
                          )}
                          {tool.permissions_required && tool.permissions_required.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {tool.permissions_required.map((perm, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">{perm}</Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No tools assigned to this agent</p>
                  )}
                </div>
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Token Management</h3>
              <p className="text-sm text-muted-foreground">
                This agent can generate tokens using Client Credentials OAuth 2.1 flow with the Client ID above. 
                Each token requires a task context (task_id) and can inherit permissions from parent tokens 
                when operating in subtasks.
              </p>
              
              <div className="bg-muted p-3 rounded-md">
                <p className="font-medium">Example Token Request:</p>
                <pre className="text-xs font-mono mt-2 overflow-auto">
{`POST /api/oauth/token
Content-Type: application/json

{
  "client_id": "${agent.client_id}",
  "client_secret": "your_client_secret",
  "grant_type": "client_credentials",
  "scope": ["read:calendar", "write:tasks"],
  "task_id": "task-123456",
  "task_description": "Read calendar events and create tasks",
  "required_tools": ["calendar_reader", "task_creator"]
}`}
                </pre>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Edit Dialog */}
      <EditAgentDialog 
        agent={agent} 
        open={editDialogOpen} 
        onOpenChange={setEditDialogOpen}
        onAgentUpdated={onUpdate}
      />
    </div>
  );
} 