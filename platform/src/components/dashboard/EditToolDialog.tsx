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
import { X, Plus } from "lucide-react";
import { useState, useEffect } from "react";
import { Tool, ToolAPI, ToolRegistration } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

// Add this interface to enhance tool parameters
interface ToolParameter {
  name: string;
  description?: string;
  required: boolean;
  type?: string;
  enum?: string[];
  format?: string;
}

interface EditToolDialogProps {
  tool: Tool;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditToolDialog({ tool, open, onOpenChange }: EditToolDialogProps) {
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
    enum: [],
    format: ""
  });
  
  // New state for managing enum values (temporary storage)
  const [enumValue, setEnumValue] = useState("");
  
  // New state for advanced JSON schema editing
  const [isJsonMode, setIsJsonMode] = useState(false);
  const [jsonSchema, setJsonSchema] = useState("");
  const [jsonError, setJsonError] = useState("");

  // Add two new states to handle the JSON Schema format
  const [schemaProperties, setSchemaProperties] = useState<Record<string, any>>({});
  const [schemaRequired, setSchemaRequired] = useState<string[]>([]);

  // Initialize form data when the dialog opens or tool changes
  useEffect(() => {
    if (open && tool) {
      // Set basic form data
      setFormData({
        name: tool.name,
        description: tool.description || "",
        category: tool.category || "",
        permissions_required: tool.permissions_required || [],
        parameters: []
      });
      
      // Handle inputSchema in JSON Schema format
      if (tool.inputSchema && 
          typeof tool.inputSchema === 'object' && 
          !Array.isArray(tool.inputSchema) &&
          'properties' in tool.inputSchema) {
        
        // Extract properties from JSON Schema
        const properties = (tool.inputSchema as any).properties || {};
        setSchemaProperties(properties);
        
        // Extract required fields
        const required = Array.isArray((tool.inputSchema as any).required) ? 
          (tool.inputSchema as any).required : [];
        setSchemaRequired(required);
        
        // Set the JSON schema editor
        setJsonSchema(JSON.stringify(tool.inputSchema, null, 2));
        
        // Convert JSON Schema properties to array of parameters for visual editor
        const params: any[] = [];
        Object.entries(properties).forEach(([name, details]: [string, any]) => {
          params.push({
            name,
            description: details.description || '',
            type: details.type || 'string',
            required: required.includes(name),
            format: details.format,
            enum: details.enum
          });
        });
        
        // Update form data with converted parameters
        setFormData(prev => ({
          ...prev,
          parameters: params
        }));
        
        // Set isJsonMode to true since we have a JSON Schema format
        setIsJsonMode(true);
      } 
      // Handle legacy array-based parameters
      else if (tool.parameters && tool.parameters.length > 0) {
        setFormData(prev => ({
          ...prev,
          parameters: tool.parameters
        }));
        
        // Convert parameters to JSON Schema properties
        const props: Record<string, any> = {};
        const req: string[] = [];
        
        tool.parameters.forEach(param => {
          if (param.name) {
            // Create property entry
            props[param.name] = {
              type: param.type || 'string',
              description: param.description
            };
            
            // Add format and enum if available
            if (param.format) {
              props[param.name].format = param.format;
            }
            
            if (param.enum && param.enum.length > 0) {
              props[param.name].enum = param.enum;
            }
            
            // Add to required list if needed
            if (param.required) {
              req.push(param.name);
            }
          }
        });
        
        setSchemaProperties(props);
        setSchemaRequired(req);
        
        // Set JSON editor with converted schema
        const schema = {
          type: 'object',
          properties: props,
          required: req.length > 0 ? req : undefined
        };
        setJsonSchema(JSON.stringify(schema, null, 2));
      }
      else if (tool.inputSchema && Array.isArray(tool.inputSchema)) {
        // Handle case where inputSchema is an array (legacy format)
        setFormData(prev => ({
          ...prev,
          parameters: tool.inputSchema as any[]
        }));
        
        // Initialize JSON schema from parameters
        setJsonSchema(JSON.stringify(tool.inputSchema, null, 2));
      }
    }
  }, [open, tool]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    
    try {
      // If in JSON mode, use the JSON editor content
      if (isJsonMode) {
        try {
          const parsedSchema = JSON.parse(jsonSchema);
          const updatedFormData = {
            ...formData,
            inputSchema: parsedSchema
          };
          
          const result = await ToolAPI.update(tool.tool_id, updatedFormData);
          toast.success(`Tool ${result.name} updated successfully`);
          onOpenChange(false);
          window.location.reload();
        } catch (error) {
          setJsonError("Invalid JSON schema");
          setIsSubmitting(false);
          return;
        }
      } else {
        // Build a JSON Schema from the individual parameters
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
            
            if (param.enum && param.enum.length > 0) {
              properties[param.name].enum = param.enum;
            }
            
            if (param.format) {
              properties[param.name].format = param.format;
            }
            
            if (param.required) {
              required.push(param.name);
            }
          }
        });
        
        // Create JSON Schema
        const jsonSchema = {
          type: 'object',
          properties: properties,
          required: required
        };
        
        // Send the update with both formats (for backward compatibility)
        const updatedFormData = {
          ...formData,
          inputSchema: jsonSchema
        };
        
        const result = await ToolAPI.update(tool.tool_id, updatedFormData);
        toast.success(`Tool ${result.name} updated successfully`);
        onOpenChange(false);
        window.location.reload();
      }
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to update tool");
    } finally {
      setIsSubmitting(false);
    }
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
  
  // Handler for adding an enum value to the new parameter
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
  
  // Handler for removing an enum value from the new parameter
  const removeEnumValue = (value: string) => {
    setNewParameter({
      ...newParameter,
      enum: newParameter.enum?.filter(v => v !== value) || []
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
    
    // Only include enum if it has values
    const paramToAdd = {
      ...newParameter,
      enum: newParameter.enum && newParameter.enum.length > 0 
        ? newParameter.enum 
        : undefined,
      format: newParameter.format && newParameter.format.trim() !== "" 
        ? newParameter.format 
        : undefined
    };
    
    setFormData({
      ...formData,
      parameters: [...(formData.parameters || []), paramToAdd]
    });
    
    // Update JSON schema
    setJsonSchema(JSON.stringify([...(formData.parameters || []), paramToAdd], null, 2));
    
    // Reset new parameter form
    setNewParameter({
      name: "",
      description: "",
      required: false,
      type: "string",
      enum: [],
      format: ""
    });
  };
  
  // Handler for removing a parameter
  const removeParameter = (paramName: string) => {
    const updatedParams = formData.parameters?.filter(p => p.name !== paramName) || [];
    setFormData({
      ...formData,
      parameters: updatedParams
    });
    
    // Update JSON schema
    setJsonSchema(JSON.stringify(updatedParams, null, 2));
  };
  
  // Handler for toggling between visual editor and JSON editor
  const toggleEditor = () => {
    if (!isJsonMode) {
      // Switching to JSON mode - convert parameters to JSON Schema
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
          
          if (param.enum && param.enum.length > 0) {
            properties[param.name].enum = param.enum;
          }
          
          if (param.format) {
            properties[param.name].format = param.format;
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
      
      setJsonSchema(JSON.stringify(schema, null, 2));
    } else {
      // Switching to visual mode - validate and parse JSON
      try {
        const parsedSchema = JSON.parse(jsonSchema);
        
        // Check if this is a JSON Schema object
        if (typeof parsedSchema === 'object' && !Array.isArray(parsedSchema) && parsedSchema.properties) {
          // Convert JSON Schema to parameters array
          const params: any[] = [];
          const required = Array.isArray(parsedSchema.required) ? parsedSchema.required : [];
          
          Object.entries(parsedSchema.properties).forEach(([name, details]: [string, any]) => {
            params.push({
              name,
              description: details.description || '',
              type: details.type || 'string',
              required: required.includes(name),
              format: details.format,
              enum: details.enum
            });
          });
          
          setFormData({
            ...formData,
            parameters: params
          });
        } else if (Array.isArray(parsedSchema)) {
          // Assume it's already an array of parameters
          setFormData({
            ...formData,
            parameters: parsedSchema
          });
        } else {
          throw new Error("Invalid schema format");
        }
        
        setJsonError("");
      } catch (error) {
        toast.error("Cannot switch to visual editor: Invalid JSON schema");
        return; // Don't toggle if JSON is invalid
      }
    }
    setIsJsonMode(!isJsonMode);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Tool</DialogTitle>
            <DialogDescription>
              Update the details for tool: {tool.name}
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
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Input Parameters</h3>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm" 
                  onClick={toggleEditor}
                  className="text-xs h-8"
                >
                  {isJsonMode ? "Visual Editor" : "JSON Editor"}
                </Button>
              </div>
              
              {isJsonMode ? (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Edit the JSON schema directly. This should follow JSON Schema format with properties and required fields.
                  </p>
                  <Textarea
                    value={jsonSchema}
                    onChange={(e) => {
                      setJsonSchema(e.target.value);
                      setJsonError("");
                    }}
                    className="font-mono text-xs h-[350px]"
                    placeholder='{"type": "object", "properties": {"param1": {"type": "string", "description": "Description"}}, "required": ["param1"]}'
                  />
                  {jsonError && (
                    <p className="text-destructive text-sm">{jsonError}</p>
                  )}
                </div>
              ) : (
                <>
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
                    
                    {/* Enum Values Section */}
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
                            {newParameter.enum.map((value: string, idx: number) => (
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
                    
                    <Button 
                      type="button" 
                      onClick={addParameter}
                      className="w-full mt-2"
                    >
                      Add Parameter
                    </Button>
                  </div>
                  
                  {/* List of Added Parameters */}
                  <div className="space-y-2 mt-4">
                    <h4 className="text-sm font-medium">Added Parameters</h4>
                    <div className="border rounded-md p-3 max-h-[250px] overflow-y-auto">
                      {formData.parameters && formData.parameters.length > 0 ? (
                        <div className="space-y-2">
                          {formData.parameters.map((param, index) => (
                            <div key={index} className="border rounded-md p-2 flex justify-between items-start">
                              <div className="flex-1">
                                <div className="font-medium">
                                  {param.name} 
                                  {param.required && <span className="text-red-500">*</span>}
                                </div>
                                {param.description && (
                                  <div className="text-sm text-muted-foreground">{param.description}</div>
                                )}
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
                  </div>
                </>
              )}
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