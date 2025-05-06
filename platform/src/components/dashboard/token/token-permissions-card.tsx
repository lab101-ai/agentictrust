"use client";

import { Token } from "@/lib/api";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { SecurityBadge, IconBadge } from "@/components/ui/icon-badge";

// Extend the Token type with optional properties that might be in the API response
interface ExtendedToken extends Token {
  requested_tools?: string[];
  owner_id?: string;
  agent_id?: string;
}

interface TokenPermissionsCardProps {
  token: ExtendedToken;
  isLoading?: boolean;
}

export const TokenPermissionsCard = ({ token, isLoading = false }: TokenPermissionsCardProps) => {
  // Normalize scope to array
  const rawScope = token.scope;
  const scopes: string[] = Array.isArray(rawScope)
    ? rawScope
    : typeof rawScope === 'string'
      ? rawScope.split(' ').filter((s: string) => s)
      : [];

  // Normalize granted_tools to array
  const rawTools = token.granted_tools;
  const tools: string[] = Array.isArray(rawTools)
    ? rawTools
    : typeof rawTools === 'string'
      ? rawTools.split(' ').filter((t: string) => t)
      : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scopes & Permissions</CardTitle>
        <CardDescription>
          Permissions granted to this token
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div>
            <p className="font-medium mb-2">Authorized Scopes:</p>
            <div className="flex flex-wrap gap-1">
              {scopes.length > 0 ? (
                scopes.map((s, idx) => (
                  <SecurityBadge key={idx} subtype="locked">{s}</SecurityBadge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>
          
          <div>
            <p className="font-medium mb-2">Granted Tools:</p>
            <div className="flex flex-wrap gap-1">
              {tools.length > 0 ? (
                tools.map((tool, idx) => (
                  <IconBadge key={idx} variant="secondary">{tool}</IconBadge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>
         
          {/* Only show requested tools section if it exists and has items */}
          {(token as ExtendedToken).requested_tools && (token as ExtendedToken).requested_tools!.length > 0 && (
            <div>
              <p className="font-medium mb-2">Requested Tools:</p>
              <div className="flex flex-wrap gap-1">
                {(token as ExtendedToken).requested_tools!.map((tool: string, idx: number) => (
                  <IconBadge key={idx} variant="outline">{tool}</IconBadge>
                ))}
              </div>
            </div>
          )}
          
          {/* Only show owner ID if it exists */}
          {(token as ExtendedToken).owner_id && (
            <div>
              <p className="font-medium mb-2">Owner ID:</p>
              <p className="font-mono text-sm break-all">{(token as ExtendedToken).owner_id}</p>
            </div>
          )}
          
          {/* Only show agent ID if it exists */}
          {(token as ExtendedToken).agent_id && (
            <div>
              <p className="font-medium mb-2">Agent ID:</p>
              <p className="font-mono text-sm break-all">{(token as ExtendedToken).agent_id}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
