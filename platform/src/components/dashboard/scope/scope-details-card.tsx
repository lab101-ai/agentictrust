"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Shield } from "lucide-react";
import { Scope } from "@/lib/api";

interface ScopeDetailsCardProps {
  scope: Scope;
  scopeCategories: string[];
  isLoading?: boolean;
  onChange: (key: string, value: any) => void;
}

export function ScopeDetailsCard({ 
  scope, 
  scopeCategories,
  isLoading = false, 
  onChange 
}: ScopeDetailsCardProps) {
  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardTitle className="text-xl flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Scope Details
        </CardTitle>
        <CardDescription>
          Configure the basic information for this OAuth scope
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Scope Name</Label>
          <Input
            id="name"
            placeholder="e.g., read:agents"
            value={scope.name}
            onChange={(e) => onChange("name", e.target.value)}
            disabled={isLoading}
          />
          <p className="text-xs text-muted-foreground">
            Use a descriptive name, typically following the format action:resource
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            placeholder="Describe what this scope allows"
            value={scope.description}
            onChange={(e) => onChange("description", e.target.value)}
            disabled={isLoading}
            rows={3}
          />
          <p className="text-xs text-muted-foreground">
            Clearly explain the permissions this scope grants to agents
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <Select
            value={scope.category}
            onValueChange={(value) => onChange("category", value)}
            disabled={isLoading}
          >
            <SelectTrigger id="category">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
              {scopeCategories.map((category) => (
                <SelectItem key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Categorize the scope by its access level
          </p>
        </div>

        <div className="space-y-4 pt-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_sensitive"
              checked={scope.is_sensitive}
              onCheckedChange={(value) => onChange("is_sensitive", Boolean(value))}
              disabled={isLoading}
            />
            <Label htmlFor="is_sensitive" className="text-sm font-normal">
              Mark as sensitive scope
            </Label>
          </div>
          <p className="text-xs text-muted-foreground ml-6">
            Sensitive scopes grant access to protected operations and resources
          </p>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_approval"
              checked={scope.requires_approval}
              onCheckedChange={(value) => onChange("requires_approval", Boolean(value))}
              disabled={isLoading}
            />
            <Label htmlFor="requires_approval" className="text-sm font-normal">
              Requires explicit approval
            </Label>
          </div>
          <p className="text-xs text-muted-foreground ml-6">
            If enabled, this scope will require explicit admin approval before being granted
          </p>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_default"
              checked={scope.is_default}
              onCheckedChange={(value) => onChange("is_default", Boolean(value))}
              disabled={isLoading}
            />
            <Label htmlFor="is_default" className="text-sm font-normal">
              Include in default scope set
            </Label>
          </div>
          <p className="text-xs text-muted-foreground ml-6">
            Default scopes are automatically included in new token requests
          </p>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_active"
              checked={scope.is_active}
              onCheckedChange={(value) => onChange("is_active", Boolean(value))}
              disabled={isLoading}
            />
            <Label htmlFor="is_active" className="text-sm font-normal">
              Scope is active
            </Label>
          </div>
          <p className="text-xs text-muted-foreground ml-6">
            Inactive scopes cannot be requested or used in policies
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
