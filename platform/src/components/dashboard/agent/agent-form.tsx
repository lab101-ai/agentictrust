"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Save } from "lucide-react";
import { AgentAPI, ToolAPI, type Tool, type Agent, type AgentRegistration } from "@/lib/api";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { AlertCircle } from "lucide-react";
import { SecurityBadge } from "@/components/ui/icon-badge";

interface AgentFormProps {
  id?: string;
  initialAgent?: Agent;
  isNew?: boolean;
}

export const AgentForm = ({ id, initialAgent, isNew = false }: AgentFormProps) => {
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  
  const [formData, setFormData] = useState<Omit<AgentRegistration, 'allowed_resources'>>(() => {
    // Initialize tool_ids from initialAgent.tools if tool_ids is not directly provided
    const initialToolIds = initialAgent?.tool_ids || initialAgent?.tools?.map(t => t.tool_id) || [];
    return {
      agent_name: initialAgent?.agent_name || "",
      description: initialAgent?.description || "",
      tool_ids: initialToolIds,
      max_scope_level: initialAgent?.max_scope_level || "restricted"
    };
  });

  // Fetch available tools
  useEffect(() => {
    const fetchAvailableTools = async () => {
      try {
        const tools = await ToolAPI.getAll();
        setAvailableTools(tools);
      } catch (err) {
        console.error("Failed to fetch tools:", err);
        toast.error("Failed to load available tools");
      } finally {
        setLoading(false);
      }
    };
    
    fetchAvailableTools();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: Omit<AgentRegistration, 'allowed_resources'>) => ({ ...prev, [name]: value }));
  };

  const handleToolChange = (toolId: string, checked: boolean) => {
    setFormData((prev: Omit<AgentRegistration, 'allowed_resources'>) => {
      if (checked) {
        return { ...prev, tool_ids: [...(prev.tool_ids || []), toolId] };
      } else {
        return { ...prev, tool_ids: (prev.tool_ids || []).filter((id: string) => id !== toolId) };
      }
    });
  };

  const handleScopeLevelChange = (value: string) => {
    setFormData((prev: Omit<AgentRegistration, 'allowed_resources'>) => ({
      ...prev,
      max_scope_level: value as "restricted" | "standard" | "elevated"
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    
    try {
      if (isNew) {
        // Create new agent
        const response = await AgentAPI.create(formData);
        toast.success("Agent created successfully");
        router.push("/dashboard?tab=agents");
      } else if (id) {
        // Update existing agent
        const updatedAgent = await AgentAPI.update(id, formData);
        toast.success("Agent updated successfully");
        router.push(`/dashboard/agents/${id}`);
      }
    } catch (err) {
      console.error("Failed to save agent:", err);
      setError("Failed to save agent. Please check your inputs and try again.");
      toast.error("Failed to save agent");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            onClick={() => router.push('/dashboard?tab=agents')} 
            className="mr-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">
            {isNew ? "New Agent" : "Edit Agent"}
          </h1>
        </div>
      </div>
      
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Agent Details</CardTitle>
              <CardDescription>
                Basic information about the agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="agent_name">Agent Name <span className="text-destructive">*</span></Label>
                <Input
                  id="agent_name"
                  name="agent_name"
                  placeholder="Enter agent name"
                  value={formData.agent_name}
                  onChange={handleInputChange}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  A unique and descriptive name for this agent
                </p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  placeholder="Enter agent description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="min-h-32"
                />
                <p className="text-sm text-muted-foreground">
                  Detailed description of the agent's purpose and behavior
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Tools & Resources</CardTitle>
              <CardDescription>
                Configure permissions and resources
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label>Authorized Tools</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {availableTools.map(tool => (
                    <div key={tool.tool_id} className="flex items-start space-x-2">
                      <Checkbox
                        id={`tool-${tool.tool_id}`}
                        checked={formData.tool_ids?.includes(tool.tool_id) || false}
                        onCheckedChange={(checked) => handleToolChange(tool.tool_id, checked as boolean)}
                      />
                      <div className="space-y-1 leading-none">
                        <label
                          htmlFor={`tool-${tool.tool_id}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {tool.name}
                        </label>
                        <p className="text-xs text-muted-foreground">
                          {tool.description ? tool.description.substring(0, 80) : 'No description'}
                          {tool.description && tool.description.length > 80 ? "..." : ""}
                        </p>
                      </div>
                    </div>
                  ))}
                  {availableTools.length === 0 && (
                    <p className="text-sm text-muted-foreground col-span-2">
                      No tools available. Please create tools first.
                    </p>
                  )}
                </div>
              </div>
              
              <div className="space-y-3">
                <Label>Maximum Scope Level</Label>
                <RadioGroup
                  value={formData.max_scope_level}
                  onValueChange={handleScopeLevelChange}
                  className="space-y-3"
                >
                  <div className="flex items-start space-x-2">
                    <RadioGroupItem value="restricted" id="restricted" />
                    <div className="space-y-1 leading-none">
                      <label
                        htmlFor="restricted"
                        className="text-sm font-medium leading-none flex items-center gap-2"
                      >
                        Restricted
                        <SecurityBadge subtype="restricted">Restricted</SecurityBadge>
                      </label>
                      <p className="text-xs text-muted-foreground">
                        Limited access to resources with strict controls
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-2">
                    <RadioGroupItem value="standard" id="standard" />
                    <div className="space-y-1 leading-none">
                      <label
                        htmlFor="standard"
                        className="text-sm font-medium leading-none flex items-center gap-2"
                      >
                        Standard
                        <SecurityBadge subtype="standard">Standard</SecurityBadge>
                      </label>
                      <p className="text-xs text-muted-foreground">
                        Normal access to most resources with regular monitoring
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-2">
                    <RadioGroupItem value="elevated" id="elevated" />
                    <div className="space-y-1 leading-none">
                      <label
                        htmlFor="elevated"
                        className="text-sm font-medium leading-none flex items-center gap-2"
                      >
                        Elevated
                        <SecurityBadge subtype="elevated">Elevated</SecurityBadge>
                      </label>
                      <p className="text-xs text-muted-foreground">
                        Full access to all resources with minimal restrictions
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="flex justify-end mt-6">
          <Button
            type="button"
            variant="outline"
            className="mr-2"
            onClick={() => router.push('/dashboard?tab=agents')} 
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isSubmitting ? "Saving..." : "Save Agent"}
          </Button>
        </div>
      </form>
    </div>
  );
};
