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
import { X, Plus } from "lucide-react";
import { useState } from "react";
import { ToolAPI, ToolRegistration } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

// Parameter type definition
interface ToolParameter {
  name: string;
  description?: string;
  required: boolean;
  type?: string;
  format?: string;
  enum?: string[];
}

export function RegisterToolDialog() {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<ToolRegistration>({
    name: "",
    description: "",
    category: "",
    permissions_required: [],
    parameters: []
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // New state for managing new permission input
  const [newPermission, setNewPermission] = useState("");
  
  // New state for managing new parameter inputs
  const [newParameter, setNewParameter] = useState<ToolParameter>({
    name: "",
    description: "",
    required: false,
    type: "string",
    format: "",
    enum: []
  });

  // Add state for managing enum values
  const [enumValue, setEnumValue] = useState("");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    
    try {
      // Build a JSON Schema from the parameters
      const properties: Record<string, any> = {};
      const required: string[] = [];
      
      // Convert parameters to properties
      formData.parameters?.forEach(param => {
        if (param.name) {
          properties[param.name] = {
            type: param.type || 'string'
          };
          
          if (param.description) {
            properties[param.name].description = param.description;
          }
          
          if (param.required) {
            required.push(param.name);
          }
        }
      });
      
      // Create JSON Schema
      const schema = {
        type: 'object',
        properties: properties,
        required: required.length > 0 ? required : undefined
      };
      
      // Include both formats for backward compatibility
      const updatedFormData = {
        ...formData,
        inputSchema: schema
      };
      
      const result = await ToolAPI.create(updatedFormData);
      toast.success(`Tool ${result.name} registered successfully`);
      handleClose(); // This will reset the form and close the dialog
      // Refresh the page to show the new tool
      window.location.reload();
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to register tool");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form data and close dialog
    setFormData({
      name: "",
      description: "",
      category: "",
      permissions_required: [],
      parameters: []
    });
    setNewPermission("");
    setNewParameter({
      name: "",
      description: "",
      required: false,
      type: "string",
      format: "",
      enum: []
    });
    setEnumValue("");
    setOpen(false);
  };
  
  // Handler for adding a new permission
  const addPermission = () => {
    if (newPermission.trim() === "") return;
    
    if (formData.permissions_required?.includes(newPermission)) {
      toast.error("This permission already exists");
      return;
    }
    
    setFormData({
      ...formData,
      permissions_required: [...(formData.permissions_required || []), newPermission]
    });
    setNewPermission("");
  };
  
  // Handler for removing a permission
  const removePermission = (permission: string) => {
    setFormData({
      ...formData,
      permissions_required: formData.permissions_required?.filter(p => p !== permission) || []
    });
  };
  
  // Handler for adding a new parameter
  const addParameter = () => {
    if (newParameter.name.trim() === "") {
      toast.error("Parameter name is required");
      return;
    }
    
    if (formData.parameters?.some(p => p.name === newParameter.name)) {
      toast.error("A parameter with this name already exists");
      return;
    }
    
    setFormData({
      ...formData,
      parameters: [...(formData.parameters || []), { ...newParameter }]
    });
    
    // Reset new parameter form
    setNewParameter({
      name: "",
      description: "",
      required: false,
      type: "string",
      format: "",
      enum: []
    });
  };
  
  // Handler for removing a parameter
  const removeParameter = (paramName: string) => {
    setFormData({
      ...formData,
      parameters: formData.parameters?.filter(p => p.name !== paramName) || []
    });
  };

  // Add handlers for enum values
  const addEnumValue = () => {
    if (enumValue.trim() === "") return;
    
    if (newParameter.enum?.includes(enumValue)) {
      toast.error("This enum value already exists");
      return;
    }
    
    setNewParameter({
      ...newParameter,
      enum: [...(newParameter.enum || []), enumValue]
    });
    setEnumValue("");
  };

  const removeEnumValue = (value: string) => {
    setNewParameter({
      ...newParameter,
      enum: newParameter.enum?.filter(v => v !== value) || []
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Register New Tool</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Register New Tool</DialogTitle>
            <DialogDescription>
              Fill in the details to register a new tool
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 gap-8 py-4">
            {/* Left Column - Basic Information */}
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Basic Information</h3>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="tool-name" className="text-right">
                      Tool Name
                    </Label>
                    <Input
                      id="tool-name"
                      value={formData.name}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                        setFormData({ ...formData, name: e.target.value })}
                      className="col-span-3"
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-4 items-start gap-4">
                    <Label htmlFor="description" className="text-right pt-2">
                      Description
                    </Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                        setFormData({ ...formData, description: e.target.value })}
                      className="col-span-3 min-h-24"
                    />
                  </div>
                  
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="category" className="text-right">
                      Category
                    </Label>
                    <Input
                      id="category"
                      value={formData.category}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                        setFormData({ ...formData, category: e.target.value })}
                      className="col-span-3"
                      placeholder="e.g., file_system, api, database"
                    />
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Permissions</h3>
                
                {/* Permissions Required Section */}
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label htmlFor="permissions" className="text-right pt-2">
                    Required
                  </Label>
                  <div className="col-span-3 space-y-2">
                    <div className="flex gap-2">
                      <Input
                        id="permissions"
                        value={newPermission}
                        onChange={(e) => setNewPermission(e.target.value)}
                        placeholder="e.g., read:files, write:database"
                        className="flex-1"
                      />
                      <Button 
                        type="button" 
                        size="sm"
                        onClick={addPermission}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                    
                    <div className="flex flex-wrap gap-2 mt-2">
                      {formData.permissions_required?.map((permission, index) => (
                        <Badge key={index} variant="secondary" className="flex items-center gap-1">
                          {permission}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-4 w-4 p-0"
                            onClick={() => removePermission(permission)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right Column - Parameters */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Input Parameters</h3>
              
              {/* Parameter Input Form */}
              <div className="border rounded-md p-3 space-y-2">
                <div className="grid grid-cols-1 gap-2">
                  <Label htmlFor="param-name">Parameter Name</Label>
                  <Input
                    id="param-name"
                    value={newParameter.name}
                    onChange={(e) => setNewParameter({...newParameter, name: e.target.value})}
                    placeholder="e.g., query, file_path"
                  />
                </div>
                
                <div className="grid grid-cols-1 gap-2">
                  <Label htmlFor="param-description">Description</Label>
                  <Input
                    id="param-description"
                    value={newParameter.description}
                    onChange={(e) => setNewParameter({...newParameter, description: e.target.value})}
                    placeholder="Describe what this parameter is for"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="param-type">Parameter Type</Label>
                    <select 
                      id="param-type"
                      value={newParameter.type}
                      onChange={(e) => setNewParameter({...newParameter, type: e.target.value})}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="integer">Integer</option>
                      <option value="boolean">Boolean</option>
                      <option value="array">Array</option>
                      <option value="object">Object</option>
                    </select>
                  </div>
                  
                  <div>
                    <Label htmlFor="param-format">Format (optional)</Label>
                    <Input
                      id="param-format"
                      value={newParameter.format || ""}
                      onChange={(e) => setNewParameter({...newParameter, format: e.target.value})}
                      placeholder="e.g., date, email, uuid"
                    />
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="param-required" 
                    checked={newParameter.required}
                    onCheckedChange={(checked) => 
                      setNewParameter({
                        ...newParameter, 
                        required: checked === true
                      })
                    }
                  />
                  <Label htmlFor="param-required">Required</Label>
                </div>
                
                {(newParameter.type === "string" || newParameter.type === "integer" || newParameter.type === "number") && (
                  <div className="mt-2">
                    <Label>Allowed Values (enum)</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={enumValue}
                        onChange={(e) => setEnumValue(e.target.value)}
                        placeholder="Add allowed value"
                        className="flex-1"
                      />
                      <Button 
                        type="button" 
                        size="sm"
                        onClick={addEnumValue}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                    
                    {newParameter.enum && newParameter.enum.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {newParameter.enum.map((value, idx) => (
                          <Badge key={idx} variant="outline" className="flex items-center gap-1">
                            {value}
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-4 w-4 p-0"
                              onClick={() => removeEnumValue(value)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                <Button 
                  type="button" 
                  onClick={addParameter}
                  className="w-full mt-2"
                >
                  Add Parameter
                </Button>
              </div>
              
              {/* List of Added Parameters */}
              <div className="border rounded-md p-3 max-h-[300px] overflow-y-auto">
                <h4 className="text-sm font-medium mb-2">Added Parameters</h4>
                {formData.parameters && formData.parameters.length > 0 ? (
                  <div className="space-y-2">
                    {formData.parameters.map((param, index) => (
                      <div key={index} className="border rounded-md p-2 flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-medium">
                            {param.name} 
                            {param.required && <span className="text-red-500">*</span>}
                          </div>
                          <div className="text-sm text-muted-foreground">{param.description || "No description"}</div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            <Badge variant="secondary">{param.type || "string"}</Badge>
                            {param.format && (
                              <Badge variant="outline">format: {param.format}</Badge>
                            )}
                          </div>
                          {param.enum && param.enum.length > 0 && (
                            <div className="mt-1">
                              <span className="text-xs text-muted-foreground">Allowed values: </span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {param.enum.map((value: string, idx: number) => (
                                  <Badge key={idx} variant="outline" className="text-xs">{value}</Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeParameter(param.name)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground text-center py-4">
                    No parameters added yet
                  </div>
                )}
              </div>
              
              <div className="text-sm text-muted-foreground">
                Parameters will be converted to a JSON Schema when saved
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
      </DialogContent>
    </Dialog>
  );
} 