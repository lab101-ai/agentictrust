"use client";

import { useState } from "react";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X, Plus, AlertCircle, Type, Hash, ToggleLeft, List, FileJson } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

// Define the parameter interface locally
interface ToolParameter {
  name: string;
  description?: string;
  required: boolean;
  type?: string;
  format?: string;
  enum?: string[];
}

interface ToolParametersCardProps {
  parameters: ToolParameter[];
  onChange: (parameters: ToolParameter[]) => void;
  isLoading?: boolean;
}

// Type badge component to display parameter types with appropriate styling
const TypeBadge = ({ type, required }: { type: string; required: boolean }) => {
  // Define icon and color for each type
  const typeConfig: Record<string, { icon: React.ElementType; className: string }> = {
    string: { icon: Type, className: "bg-blue-500 hover:bg-blue-500/90 text-white" },
    number: { icon: Hash, className: "bg-green-600 hover:bg-green-600/90 text-white" },
    boolean: { icon: ToggleLeft, className: "bg-purple-600 hover:bg-purple-600/90 text-white" },
    array: { icon: List, className: "bg-amber-500 hover:bg-amber-500/90 text-white" },
    object: { icon: FileJson, className: "bg-slate-700 hover:bg-slate-700/90 text-white" }
  };
  
  const config = typeConfig[type] || typeConfig.string;
  
  return (
    <Badge className={cn(config.className)}>
      <config.icon className="h-3 w-3 mr-1" />
      {type}{required ? "*" : ""}
    </Badge>
  );
};

export const ToolParametersCard = ({ 
  parameters, 
  onChange,
  isLoading = false
}: ToolParametersCardProps) => {
  const [newParameter, setNewParameter] = useState<ToolParameter>({
    name: "",
    description: "",
    required: false,
    type: "string",
    format: "",
    enum: []
  });
  
  const [enumValue, setEnumValue] = useState("");
  
  // Handler for adding a new parameter
  const addParameter = () => {
    if (newParameter.name.trim() === "") {
      return;
    }
    
    if (parameters.some(p => p.name === newParameter.name)) {
      return;
    }
    
    onChange([...parameters, { ...newParameter }]);
    
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
    onChange(parameters.filter(p => p.name !== paramName));
  };
  
  // Add handlers for enum values
  const addEnumValue = () => {
    if (enumValue.trim() === "") return;
    
    if (newParameter.enum?.includes(enumValue)) {
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
    <Card>
      <CardHeader>
        <CardTitle>Tool Parameters</CardTitle>
        <CardDescription>
          Define the parameters required by this tool. * means required
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          {parameters.length > 0 ? (
            parameters.map((param, index) => (
              <div key={index} className="flex flex-col p-3 border rounded-md relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 h-6 w-6"
                  onClick={() => removeParameter(param.name)}
                  disabled={isLoading}
                >
                  <X className="h-4 w-4" />
                </Button>
                
                <div className="mb-2">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="font-medium">{param.name}</div>
                    <TypeBadge type={param.type || "string"} required={!!param.required} />
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {param.description || "No description provided."}
                  </div>
                </div>
                
                {param.format && (
                  <div className="mb-2">
                    <Label>Format</Label>
                    <div>{param.format}</div>
                  </div>
                )}
                
                {param.enum && param.enum.length > 0 && (
                  <div>
                    <Label>Enum Values</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {param.enum.map((value, i) => (
                        <Badge key={i} variant="outline">{value}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No parameters defined. Add parameters below.
              </AlertDescription>
            </Alert>
          )}
        </div>
        
        <div className="border-t pt-4 mt-6">
          <h4 className="font-medium mb-2">Add New Parameter</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label htmlFor="param-name">Name</Label>
              <Input
                id="param-name"
                value={newParameter.name}
                onChange={(e) => setNewParameter({...newParameter, name: e.target.value})}
                placeholder="Parameter name"
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="param-type">Type</Label>
              <Select
                value={newParameter.type || "string"}
                onValueChange={(value) => setNewParameter({...newParameter, type: value})}
                disabled={isLoading}
              >
                <SelectTrigger id="param-type">
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="string">
                    <div className="flex items-center">
                      <Type className="h-3 w-3 mr-2 text-blue-500" />
                      <span>String</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="number">
                    <div className="flex items-center">
                      <Hash className="h-3 w-3 mr-2 text-green-600" />
                      <span>Number</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="boolean">
                    <div className="flex items-center">
                      <ToggleLeft className="h-3 w-3 mr-2 text-purple-600" />
                      <span>Boolean</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="array">
                    <div className="flex items-center">
                      <List className="h-3 w-3 mr-2 text-amber-500" />
                      <span>Array</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="object">
                    <div className="flex items-center">
                      <FileJson className="h-3 w-3 mr-2 text-slate-700" />
                      <span>Object</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-2 mb-4">
            <Label htmlFor="param-description">Description</Label>
            <Textarea
              id="param-description"
              value={newParameter.description || ""}
              onChange={(e) => setNewParameter({...newParameter, description: e.target.value})}
              placeholder="Parameter description"
              disabled={isLoading}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label htmlFor="param-format">Format (optional)</Label>
              <Input
                id="param-format"
                value={newParameter.format || ""}
                onChange={(e) => setNewParameter({...newParameter, format: e.target.value})}
                placeholder="e.g. date-time, email, uri"
                disabled={isLoading}
              />
            </div>
            
            <div className="flex items-center space-x-2 h-10 mt-8">
              <Checkbox
                id="param-required"
                checked={newParameter.required}
                onCheckedChange={(checked) => 
                  setNewParameter({...newParameter, required: !!checked})
                }
                disabled={isLoading}
              />
              <Label htmlFor="param-required">Required parameter</Label>
            </div>
          </div>
          
          {newParameter.type === "string" && (
            <div className="space-y-4 mb-4 border rounded-md p-3">
              <Label>Enum Values (optional)</Label>
              <div className="flex items-center space-x-2">
                <Input
                  value={enumValue}
                  onChange={(e) => setEnumValue(e.target.value)}
                  placeholder="Add an enum value"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addEnumValue}
                  disabled={isLoading || !enumValue.trim()}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
              {newParameter.enum && newParameter.enum.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {newParameter.enum.map((value, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {value}
                      <button 
                        type="button" 
                        onClick={() => removeEnumValue(value)}
                        className="rounded-full h-4 w-4 inline-flex items-center justify-center text-xs"
                        disabled={isLoading}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
          
          <Button
            type="button"
            onClick={addParameter}
            disabled={isLoading || !newParameter.name.trim()}
            className="mt-2"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Parameter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
