"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Policy, Scope } from "@/lib/api";

interface PolicyDetailsCardProps {
  policy: Policy;
  scopes: Scope[];
  onPolicyChange: (key: string, value: any) => void;
}

export function PolicyDetailsCard({ policy, scopes, onPolicyChange }: PolicyDetailsCardProps) {
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    onPolicyChange(name, value);
  };

  const handleSelectChange = (name: string, value: string) => {
    onPolicyChange(name, value);
  };

  const handleSwitchChange = (name: string, checked: boolean) => {
    onPolicyChange(name, checked);
  };

  const handleScopeToggle = (scopeId: string, checked: boolean) => {
    let updated = Array.isArray(policy.scopes) ? [...policy.scopes] : [];
    if (checked) {
      if (!updated.includes(scopeId)) updated.push(scopeId);
    } else {
      updated = updated.filter((id) => id !== scopeId);
    }
    onPolicyChange("scopes", updated);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle>Policy Details</CardTitle>
          <CardDescription>
            Basic information about this access control policy
          </CardDescription>
        </div>
        <div className="flex items-center space-x-2">
          <Label htmlFor="is_active" className="text-sm">Active</Label>
          <Switch
            id="is_active"
            checked={policy.is_active}
            onCheckedChange={(checked) => handleSwitchChange("is_active", checked)}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Policy Name</Label>
          <Input
            id="name"
            name="name"
            value={policy.name}
            onChange={handleChange}
            placeholder="Enter policy name"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            name="description"
            value={policy.description || ""}
            onChange={handleChange}
            placeholder="Policy description (optional)"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="effect">Effect</Label>
            <Select
              value={policy.effect}
              onValueChange={(value) => handleSelectChange("effect", value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select effect" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="allow">Allow</SelectItem>
                <SelectItem value="deny">Deny</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2 col-span-2">
            <Label>Scopes</Label>
            <div className="border rounded-md p-3 max-h-60 overflow-y-auto">
              {/* Group scopes by category */}
              {Object.entries(
                scopes.reduce<Record<string, Scope[]>>((acc, scope) => {
                  const category = scope.category || 'Other';
                  if (!acc[category]) acc[category] = [];
                  acc[category].push(scope);
                  return acc;
                }, {})
              ).map(([category, categoryScopes]) => (
                <div key={category} className="mb-4 last:mb-0">
                  <h4 className="text-sm font-medium mb-2 text-muted-foreground">{category}</h4>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                    {categoryScopes.map((scope) => (
                      <label key={scope.scope_id} className="flex items-center space-x-2 text-sm border-b border-border/30 pb-1 hover:bg-accent/10 rounded px-1">
                        <Checkbox
                          checked={policy.scopes?.includes(scope.scope_id) || false}
                          onCheckedChange={(checked) => handleScopeToggle(scope.scope_id, !!checked)}
                          className="data-[state=checked]:bg-primary"
                        />
                        <span className="overflow-hidden text-ellipsis whitespace-nowrap">{scope.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Input
              id="priority"
              name="priority"
              type="number"
              value={policy.priority.toString()}
              onChange={handleChange}
              min={0}
              max={100}
              required
            />
            <p className="text-xs text-muted-foreground">
              Higher priority policies (0-100) are evaluated first
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
