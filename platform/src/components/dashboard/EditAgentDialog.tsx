"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { AgentAPI, ToolAPI, Tool, Agent } from "@/lib/api";
import { toast } from "sonner";

interface EditAgentDialogProps {
  agent: Agent;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditAgentDialog({ agent, open, onOpenChange }: EditAgentDialogProps) {
  const [formData, setFormData] = useState({
    agent_name: "",
    description: "",
    tool_ids: [] as string[],
    allowed_resources: [] as string[],
    max_scope_level: "restricted" as "restricted" | "standard" | "elevated"
  });
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Available resources
  const availableResources = [
    { id: "github", name: "GitHub", description: "Access to GitHub repositories and issues" },
    { id: "jira", name: "Jira", description: "Access to Jira projects, issues, and workflows" },
    { id: "s3", name: "AWS S3", description: "Read/write access to S3 buckets and objects" },
    { id: "gmail", name: "Gmail", description: "Access to send and read emails" },
    { id: "gdrive", name: "Google Drive", description: "Access to Google Drive files and folders" },
    { id: "slack", name: "Slack", description: "Send and read messages in Slack channels" },
    { id: "calendar", name: "Calendar", description: "Access to read and create calendar events" },
  ];
  
  // Scope level descriptions
  const scopeLevels = [
    { 
      value: "restricted", 
      label: "Restricted", 
      description: "Minimal access with strict rate limits and required approvals for sensitive operations" 
    },
    { 
      value: "standard", 
      label: "Standard", 
      description: "Regular access to common resources with moderate rate limits and approvals for critical operations" 
    },
    { 
      value: "elevated", 
      label: "Elevated", 
      description: "Higher access levels with fewer rate limits and approvals for trusted agents" 
    }
  ];

  // Initialize form data when dialog opens
  useEffect(() => {
    if (open && agent) {
      setFormData({
        agent_name: agent.agent_name,
        description: agent.description || "",
        tool_ids: agent.allowed_tools || [],
        allowed_resources: agent.allowed_resources || [],
        max_scope_level: (agent.max_scope_level as "restricted" | "standard" | "elevated") || "restricted"
      });
      
      // Fetch available tools
      const fetchTools = async () => {
        try {
          const tools = await ToolAPI.getAll();
          setAvailableTools(tools);
        } catch (error) {
          // Error handled by toast
          toast.error("Failed to load available tools");
        }
      };
      fetchTools();
    }
  }, [open, agent]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    
    try {
      const result = await AgentAPI.update(agent.client_id, {
        agent_name: formData.agent_name,
        description: formData.description,
        allowed_resources: formData.allowed_resources,
        max_scope_level: formData.max_scope_level,
        tool_ids: formData.tool_ids
      });
      
      toast.success(`Agent ${result.agent_name} updated successfully`);
      onOpenChange(false);
      // Refresh the page to show updated data
      window.location.reload();
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to update agent");
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Group tools by category
  const toolsByCategory = availableTools.reduce((acc, tool) => {
    const category = tool.category || 'Uncategorized';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(tool);
    return acc;
  }, {} as Record<string, Tool[]>);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Agent</DialogTitle>
            <DialogDescription>
              Update configuration for agent: {agent.agent_name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-5 items-center gap-4">
              <Label htmlFor="agent-name" className="text-right col-span-1">
                Agent Name
              </Label>
              <div className="col-span-4">
                <Input
                  id="agent-name"
                  value={formData.agent_name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                    setFormData({ ...formData, agent_name: e.target.value })}
                  required
                  placeholder="e.g., Calendar Assistant, Data Processor"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Choose a descriptive name that identifies the agent's purpose
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-5 items-start gap-4">
              <Label htmlFor="description" className="text-right pt-2 col-span-1">
                Description
              </Label>
              <div className="col-span-4">
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                    setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this agent does and its intended use cases"
                  className="min-h-24"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  A detailed description helps track the agent's purpose and approved workflows
                </p>
              </div>
            </div>
            
            <div className="my-2 border-t pt-4">
              <h3 className="text-md font-medium mb-2">Access Controls & Permissions</h3>
            </div>
            
            {/* Scope Level Section */}
            <div className="grid grid-cols-5 items-start gap-4">
              <Label className="text-right pt-2 col-span-1">
                Scope Level
              </Label>
              <div className="col-span-4">
                <RadioGroup 
                  value={formData.max_scope_level}
                  onValueChange={(value: "restricted" | "standard" | "elevated") => 
                    setFormData({ ...formData, max_scope_level: value })}
                  className="space-y-3"
                >
                  {scopeLevels.map((scope) => (
                    <div key={scope.value} className="flex items-start space-x-2 border rounded-md p-3 hover:bg-accent transition-colors">
                      <RadioGroupItem value={scope.value} id={`scope-${scope.value}`} className="mt-1" />
                      <div>
                        <Label htmlFor={`scope-${scope.value}`} className="font-medium">{scope.label}</Label>
                        <p className="text-sm text-muted-foreground">{scope.description}</p>
                      </div>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </div>
            
            {/* Allowed Resources Section */}
            <div className="grid grid-cols-5 items-start gap-4 mt-2">
              <Label className="text-right pt-2 col-span-1">
                Allowed Resources
              </Label>
              <div className="col-span-4">
                <div className="space-y-3">
                  {availableResources.map((resource) => (
                    <div key={resource.id} className="flex items-start space-x-2 border rounded-md p-3 hover:bg-accent transition-colors">
                      <Checkbox 
                        id={`resource-${resource.id}`} 
                        checked={formData.allowed_resources?.includes(resource.id)}
                        onCheckedChange={(checked: boolean | "indeterminate") => {
                          if (checked === true) {
                            setFormData({ 
                              ...formData, 
                              allowed_resources: [...(formData.allowed_resources || []), resource.id] 
                            });
                          } else {
                            setFormData({ 
                              ...formData, 
                              allowed_resources: formData.allowed_resources?.filter(id => id !== resource.id) || []
                            });
                          }
                        }}
                        className="mt-1"
                      />
                      <div>
                        <Label htmlFor={`resource-${resource.id}`} className="font-medium">{resource.name}</Label>
                        <p className="text-sm text-muted-foreground">{resource.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Select only the resources this agent needs access to (principle of least privilege)
                </p>
              </div>
            </div>
            
            {/* Tools Section */}
            <div className="grid grid-cols-5 items-start gap-4 mt-2">
              <Label className="text-right pt-2 col-span-1">
                Allowed Tools
              </Label>
              <div className="col-span-4">
                {availableTools.length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(toolsByCategory).map(([category, tools]) => (
                      <div key={category} className="space-y-2">
                        <h4 className="font-medium border-b pb-1">{category}</h4>
                        <div className="grid grid-cols-1 gap-2">
                          {tools.map((tool) => (
                            <div key={tool.tool_id} className="flex items-start space-x-2 border rounded-md p-3 hover:bg-accent transition-colors">
                              <Checkbox 
                                id={`tool-${tool.tool_id}`} 
                                checked={formData.tool_ids?.includes(tool.tool_id)}
                                onCheckedChange={(checked: boolean | "indeterminate") => {
                                  if (checked === true) {
                                    setFormData({ 
                                      ...formData, 
                                      tool_ids: [...(formData.tool_ids || []), tool.tool_id] 
                                    });
                                  } else {
                                    setFormData({ 
                                      ...formData, 
                                      tool_ids: formData.tool_ids?.filter(id => id !== tool.tool_id) || []
                                    });
                                  }
                                }}
                                className="mt-1"
                              />
                              <div className="w-full">
                                <div className="flex justify-between items-start">
                                  <Label htmlFor={`tool-${tool.tool_id}`} className="font-medium">{tool.name}</Label>
                                  {!tool.is_active && (
                                    <Badge variant="outline" className="ml-2">Inactive</Badge>
                                  )}
                                </div>
                                <p className="text-sm text-muted-foreground">{tool.description || "No description provided"}</p>
                                {tool.permissions_required && tool.permissions_required.length > 0 && (
                                  <div className="mt-2">
                                    <span className="text-xs text-muted-foreground">Required permissions:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {tool.permissions_required.map((perm, idx) => (
                                        <Badge key={idx} variant="secondary" className="text-xs">{perm}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 border rounded-md">
                    <p className="text-muted-foreground">Loading tools...</p>
                  </div>
                )}
                
                <div className="flex justify-between items-center mt-4">
                  <p className="text-xs text-muted-foreground">
                    Selected tools: {formData.tool_ids?.length || 0}
                  </p>
                  {formData.tool_ids && formData.tool_ids.length > 0 && (
                    <Button 
                      type="button" 
                      variant="outline" 
                      size="sm"
                      onClick={() => setFormData({ ...formData, tool_ids: [] })}
                    >
                      Clear Selection
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Updating..." : "Update"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 