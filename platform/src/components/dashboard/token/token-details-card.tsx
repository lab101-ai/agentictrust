"use client";

import { Token } from "@/lib/api";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { StatusBadge, SecurityBadge, TimeBadge, IconBadge } from "@/components/ui/icon-badge";

interface TokenDetailsCardProps {
  token: Token;
  isLoading?: boolean;
}

export const TokenDetailsCard = ({ token, isLoading = false }: TokenDetailsCardProps) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle>Token Details</CardTitle>
          <CardDescription>
            Basic information about this token
          </CardDescription>
        </div>
        <div>
          {token.is_revoked ? (
            <SecurityBadge subtype="warning">Revoked</SecurityBadge>
          ) : token.exp * 1000 < Date.now() ? (
            <TimeBadge subtype="expired">Expired</TimeBadge>
          ) : (
            <StatusBadge subtype="success">Active</StatusBadge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-4 items-start gap-3">
          <p className="font-medium text-right text-muted-foreground">ID:</p>
          <p className="col-span-3 font-mono text-sm break-all">{token.token_id}</p>
          
          <p className="font-medium text-right text-muted-foreground">Client ID:</p>
          <p className="col-span-3 font-mono text-sm break-all">{token.client_id}</p>

          {/* --- OIDC-A Agent Identity Claims --- */}
          {token.agent_instance_id && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Instance ID:</p>
              <p className="col-span-3 font-mono text-sm break-all">{token.agent_instance_id}</p>
            </>
          )}
          {token.agent_type && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Type:</p>
              <p className="col-span-3">{token.agent_type}</p>
            </>
          )}
          {token.agent_model && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Model:</p>
              <p className="col-span-3">{token.agent_model}</p>
            </>
          )}
          {token.agent_version && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Version:</p>
              <p className="col-span-3">{token.agent_version}</p>
            </>
          )}
           {token.agent_provider && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Provider:</p>
              <p className="col-span-3">{token.agent_provider}</p>
            </>
          )}
          {token.agent_trust_level && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Trust Level:</p>
              <p className="col-span-3">{token.agent_trust_level}</p>
            </>
          )}
          {token.agent_context_id && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Context ID:</p>
              <p className="col-span-3 font-mono text-sm break-all">{token.agent_context_id}</p>
            </>
          )}

          {/* --- OIDC-A Delegation Claims --- */}
          {token.delegator_sub && (
            <>
              <p className="font-medium text-right text-muted-foreground">Delegator Sub:</p>
              <p className="col-span-3 font-mono text-sm break-all">{token.delegator_sub}</p>
            </>
          )}
          {token.delegation_purpose && (
            <>
              <p className="font-medium text-right text-muted-foreground">Delegation Purpose:</p>
              <p className="col-span-3">{token.delegation_purpose}</p>
            </>
          )}
          {token.delegation_chain && (
            <>
              <p className="font-medium text-right text-muted-foreground">Delegation Chain:</p>
              <pre className="col-span-3 font-mono text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify(token.delegation_chain, null, 2)}
              </pre>
            </>
          )}
          {token.delegation_constraints && (
            <>
              <p className="font-medium text-right text-muted-foreground">Delegation Constraints:</p>
              <pre className="col-span-3 font-mono text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify(token.delegation_constraints, null, 2)}
              </pre>
            </>
          )}

          {/* --- OIDC-A Agent Capability/Attestation Claims --- */}
          {token.agent_capabilities && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Capabilities:</p>
              <pre className="col-span-3 font-mono text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify(token.agent_capabilities, null, 2)}
              </pre>
            </>
          )}
           {token.agent_attestation && (
            <>
              <p className="font-medium text-right text-muted-foreground">Agent Attestation:</p>
              <pre className="col-span-3 font-mono text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify(token.agent_attestation, null, 2)}
              </pre>
            </>
          )}
          
          {/* --- Custom/Other Claims --- */}
          <p className="font-medium text-right text-muted-foreground">Task ID:</p>
          <p className="col-span-3 font-mono text-sm break-all">{token.task_id || 'N/A'}</p>
          
          {token.parent_task_id && (
            <>
              <p className="font-medium text-right text-muted-foreground">Parent Task ID:</p>
              <p className="col-span-3 font-mono text-sm break-all">{token.parent_task_id}</p>
            </>
          )}
          
          {token.parent_token_id && (
            <>
              <p className="font-medium text-right text-muted-foreground">Parent Token ID:</p>
              <p className="col-span-3 font-mono text-sm break-all">{token.parent_token_id}</p>
            </>
          )}
          
          <p className="font-medium text-right text-muted-foreground">Issued At (iat):</p>
          <p className="col-span-3">{new Date(token.iat * 1000).toLocaleString()} ({token.iat})</p>
          
          <p className="font-medium text-right text-muted-foreground">Expires At (exp):</p>
          <p className="col-span-3">{new Date(token.exp * 1000).toLocaleString()} ({token.exp})</p>
          
          {token.is_revoked && (
            <>
              <p className="font-medium text-right text-muted-foreground">Revoked At:</p>
              <p className="col-span-3">{token.revoked_at ? new Date(token.revoked_at).toLocaleString() : 'N/A'}</p>
              
              <p className="font-medium text-right text-muted-foreground">Revocation Reason:</p>
              <p className="col-span-3">{token.revocation_reason || 'No reason provided'}</p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
