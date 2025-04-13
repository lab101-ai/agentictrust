"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Copy, Check, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { AgentAPI, ToolAPI, Tool, AgentRegistration, AgentCredentials } from "@/lib/api";
import { toast } from "sonner";

interface RegisterAgentDialogProps {
  onAgentAdded?: () => Promise<void> | void;
}

export function RegisterAgentDialog({ onAgentAdded }: RegisterAgentDialogProps) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<AgentRegistration>({
    agent_name: "",
    description: "",
    tool_ids: [],
    allowed_resources: [],
    max_scope_level: "restricted"
  });
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [credentials, setCredentials] = useState<AgentCredentials | null>(null);
  
  // Clipboard state for copying credentials
  const [copied, setCopied] = useState<{
    clientId: boolean;
    clientSecret: boolean;
    registrationToken: boolean;
  }>({
    clientId: false,
    clientSecret: false,
    registrationToken: false,
  });

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

  // Fetch tools when dialog opens
  useEffect(() => {
    if (open) {
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
  }, [open]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    
    try {
      const result = await AgentAPI.create(formData);
      toast.success(`Agent ${result.agent_name} registered successfully`);
      setCredentials(result.credentials);
      
      // Call the callback if provided
      if (onAgentAdded) {
        onAgentAdded();
      }
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to register agent");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form data and close dialog
    setFormData({
      agent_name: "",
      description: "",
      tool_ids: [],
      allowed_resources: [],
      max_scope_level: "restricted"
    });
    setCredentials(null);
    setCopied({
      clientId: false,
      clientSecret: false,
      registrationToken: false,
    });
    setOpen(false);
  };
  
  const copyToClipboard = async (text: string, field: 'clientId' | 'clientSecret' | 'registrationToken') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied({ ...copied, [field]: true });
      setTimeout(() => setCopied({ ...copied, [field]: false }), 2000);
    } catch (err) {
      // Error is not critical
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
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Register New Agent</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        {credentials ? (
          // Show credentials after successful registration
          <>
            <DialogHeader>
              <DialogTitle>Agent Registered Successfully</DialogTitle>
              <DialogDescription>
                Store these credentials securely. They will not be shown again.
              </DialogDescription>
            </DialogHeader>
            
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-3 rounded-md my-4 flex gap-2">
              <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-amber-800 dark:text-amber-400">Security Warning</h4>
                <p className="text-sm text-amber-700 dark:text-amber-300">These credentials grant access to your resources. Never share them publicly or commit them to version control.</p>
              </div>
            </div>
            
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-5 items-center gap-2">
                <Label className="text-right font-medium col-span-1">Client ID:</Label>
                <div className="relative col-span-4">
                  <code className="bg-muted p-2 rounded text-sm break-all block w-full">
                    {credentials.client_id}
                  </code>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm" 
                    className="absolute right-1 top-1"
                    onClick={() => copyToClipboard(credentials.client_id, 'clientId')}
                  >
                    {copied.clientId ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-5 items-center gap-2">
                <Label className="text-right font-medium col-span-1">Client Secret:</Label>
                <div className="relative col-span-4">
                  <code className="bg-muted p-2 rounded text-sm break-all block w-full">
                    {credentials.client_secret}
                  </code>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm" 
                    className="absolute right-1 top-1"
                    onClick={() => copyToClipboard(credentials.client_secret, 'clientSecret')}
                  >
                    {copied.clientSecret ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-5 items-center gap-2">
                <Label className="text-right font-medium col-span-1">Registration Token:</Label>
                <div className="relative col-span-4">
                  <code className="bg-muted p-2 rounded text-sm break-all block w-full">
                    {credentials.registration_token}
                  </code>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm" 
                    className="absolute right-1 top-1"
                    onClick={() => copyToClipboard(credentials.registration_token, 'registrationToken')}
                  >
                    {copied.registrationToken ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <div className="mt-2 text-sm text-muted-foreground">
                <p><strong>Next steps:</strong></p>
                <ol className="list-decimal pl-5 space-y-1">
                  <li>Store these credentials in a secure location</li>
                  <li>Use the Client ID and Secret for authenticating API requests</li>
                  <li>Activate the agent if not immediately active</li>
                </ol>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleClose}>Close</Button>
            </DialogFooter>
          </>
        ) : (
          // Registration form
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Register New Agent</DialogTitle>
              <DialogDescription>
                Configure your AI agent's identity, permissions, and access levels
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
                    onValueChange={(value: string) => setFormData({ ...formData, max_scope_level: value })}
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
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Registering..." : "Register"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
} 