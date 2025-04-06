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
import { useState } from "react";

export function RegisterAgentDialog() {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    agentName: "",
    description: "",
    tools: [] as string[],
    resources: [] as string[],
    scopeLevel: "restricted"
  });

  // Mock available tools
  const availableTools = [
    { id: "tool-123", name: "Calendar API" },
    { id: "tool-456", name: "File Reader" },
    { id: "tool-789", name: "Data Analyzer" },
  ];

  // Mock available resources
  const availableResources = [
    { id: "github", name: "GitHub" },
    { id: "jira", name: "Jira" },
    { id: "s3", name: "S3" },
  ];

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    console.log("Registering agent:", formData);
    
    // TODO: Make API call to register agent
    
    // Reset form and close dialog
    setFormData({
      agentName: "",
      description: "",
      tools: [],
      resources: [],
      scopeLevel: "restricted"
    });
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Register New Agent</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Register New Agent</DialogTitle>
            <DialogDescription>
              Fill in the details to register a new AI agent
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="agent-name" className="text-right">
                Agent Name
              </Label>
              <Input
                id="agent-name"
                value={formData.agentName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                  setFormData({ ...formData, agentName: e.target.value })}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="description" className="text-right">
                Description
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                  setFormData({ ...formData, description: e.target.value })}
                className="col-span-3"
              />
            </div>
            
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">Allowed Tools</Label>
              <div className="col-span-3 space-y-2">
                {availableTools.map((tool) => (
                  <div key={tool.id} className="flex items-center space-x-2">
                    <Checkbox 
                      id={`tool-${tool.id}`} 
                      checked={formData.tools.includes(tool.id)}
                      onCheckedChange={(checked: boolean | "indeterminate") => {
                        if (checked === true) {
                          setFormData({ ...formData, tools: [...formData.tools, tool.id] });
                        } else {
                          setFormData({ 
                            ...formData, 
                            tools: formData.tools.filter(id => id !== tool.id) 
                          });
                        }
                      }}
                    />
                    <Label htmlFor={`tool-${tool.id}`}>{tool.name}</Label>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">Allowed Resources</Label>
              <div className="col-span-3 space-y-2">
                {availableResources.map((resource) => (
                  <div key={resource.id} className="flex items-center space-x-2">
                    <Checkbox 
                      id={`resource-${resource.id}`} 
                      checked={formData.resources.includes(resource.id)}
                      onCheckedChange={(checked: boolean | "indeterminate") => {
                        if (checked === true) {
                          setFormData({ ...formData, resources: [...formData.resources, resource.id] });
                        } else {
                          setFormData({ 
                            ...formData, 
                            resources: formData.resources.filter(id => id !== resource.id) 
                          });
                        }
                      }}
                    />
                    <Label htmlFor={`resource-${resource.id}`}>{resource.name}</Label>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">Scope Level</Label>
              <RadioGroup 
                className="col-span-3"
                value={formData.scopeLevel}
                onValueChange={(value: string) => setFormData({ ...formData, scopeLevel: value })}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="restricted" id="scope-restricted" />
                  <Label htmlFor="scope-restricted">Restricted</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="standard" id="scope-standard" />
                  <Label htmlFor="scope-standard">Standard</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="elevated" id="scope-elevated" />
                  <Label htmlFor="scope-elevated">Elevated</Label>
                </div>
              </RadioGroup>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit">Register</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 