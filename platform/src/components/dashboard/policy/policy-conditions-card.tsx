"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";

interface PolicyConditionsCardProps {
  conditionsString: string;
  conditionsError: string | null;
  onConditionsChange: (value: string, parsed: any) => void;
}

export function PolicyConditionsCard({ 
  conditionsString, 
  conditionsError, 
  onConditionsChange
}: PolicyConditionsCardProps) {
  const handleConditionsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    try {
      const parsed = JSON.parse(value);
      onConditionsChange(value, parsed);
    } catch (error) {
      // Pass the unparsed value with null to indicate there's an error
      onConditionsChange(value, null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Policy Conditions</CardTitle>
        <CardDescription>
          JSON conditions that determine when this policy applies
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="conditions" className={conditionsError ? "text-destructive" : ""}>
              Conditions (JSON)
            </Label>
            {conditionsError && (
              <span className="text-sm font-medium text-destructive">
                {conditionsError}
              </span>
            )}
          </div>
          <Textarea
            id="conditions"
            value={conditionsString}
            onChange={handleConditionsChange}
            placeholder="{}"
            rows={15}
            className={`font-mono ${conditionsError ? "border-destructive" : ""}`}
          />
          <p className="text-xs text-muted-foreground">
            Conditions define when the policy applies. Use JSON format.
          </p>
        </div>
      </CardContent>
      <CardFooter className="border-t px-6 py-4 text-sm text-muted-foreground">
        <p>
          Use dot notation to access attributes: agent.role, resource.owner_id, etc.
        </p>
      </CardFooter>
    </Card>
  );
}
