"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Scope, Tool, ToolRegistration } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { IconBadge } from "@/components/ui/icon-badge";
import { X, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ToolDetailsCardProps {
  tool: Tool | ToolRegistration;
  scopes?: Scope[];
  isLoading?: boolean;
  onChange?: (key: string, value: any) => void;
}

export const ToolDetailsCard = ({ 
  tool, 
  scopes = [], 
  isLoading = false, 
  onChange
}: ToolDetailsCardProps) => {
  const [scopeSearch, setScopeSearch] = useState("");
  
  const handleChange = (key: string, value: any) => {
    if (onChange) {
      onChange(key, value);
    }
  };

  const filteredScopes = scopes.filter(scope => 
    scope.name.toLowerCase().includes(scopeSearch.toLowerCase()) ||
    scope.description.toLowerCase().includes(scopeSearch.toLowerCase())
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tool Details</CardTitle>
        <CardDescription>
          Basic information about this tool
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input 
            id="name" 
            placeholder="Enter tool name" 
            value={(tool as any).name || ""}
            onChange={(e) => handleChange("name", e.target.value)}
            disabled={isLoading}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea 
            id="description" 
            placeholder="Describe what this tool does" 
            value={(tool as any).description || ""}
            onChange={(e) => handleChange("description", e.target.value)}
            disabled={isLoading}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select 
            value={(tool as any).category || ""} 
            onValueChange={(value) => handleChange("category", value)}
            disabled={isLoading}
          >
            <SelectTrigger id="category">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="productivity">Productivity</SelectItem>
              <SelectItem value="analytics">Analytics</SelectItem>
              <SelectItem value="communication">Communication</SelectItem>
              <SelectItem value="utility">Utility</SelectItem>
              <SelectItem value="ai">AI</SelectItem>
              <SelectItem value="integration">Integration</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-2">
          <Label>Required Permissions</Label>
          <div className="flex items-center space-x-2 py-2">
            <Input
              placeholder="Search scopes..."
              value={scopeSearch}
              onChange={(e) => setScopeSearch(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          {scopes.length === 0 && !isLoading && (
            <Alert variant="destructive" className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No scopes available. Create scopes first.
              </AlertDescription>
            </Alert>
          )}
          
          <div className="max-h-40 overflow-y-auto border rounded-md p-2">
            {filteredScopes.map((scope) => {
              const isChecked = Array.isArray(tool.permissions_required) && tool.permissions_required.includes(scope.scope_id);
              return (
                <div key={scope.scope_id} className="flex items-center space-x-2 py-1">
                  <Checkbox
                    id={`scope-${scope.scope_id}`}
                    checked={isChecked}
                    onCheckedChange={(checked) => {
                      const currentPermissions = Array.isArray(tool.permissions_required) ? [...tool.permissions_required] : [];
                      if (checked) {
                        if (!currentPermissions.includes(scope.scope_id)) {
                          handleChange("permissions_required", [...currentPermissions, scope.scope_id]);
                        }
                      } else {
                        handleChange(
                          "permissions_required",
                          currentPermissions.filter((id) => id !== scope.scope_id)
                        );
                      }
                    }}
                    disabled={isLoading}
                  />
                  <Label
                    htmlFor={`scope-${scope.scope_id}`}
                    className="text-sm cursor-pointer flex items-center space-x-2"
                  >
                    <span>{scope.name}</span>
                    <IconBadge variant="secondary">{scope.category}</IconBadge>
                  </Label>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="flex items-center space-x-2 pt-4">
          <Switch
            id="is_active"
            checked={(tool as any).is_active !== false}
            onCheckedChange={(checked) => handleChange("is_active", checked)}
            disabled={isLoading}
          />
          <Label htmlFor="is_active">Tool is active</Label>
        </div>
      </CardContent>
    </Card>
  );
}
