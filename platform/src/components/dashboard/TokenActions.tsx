"use client";

import { useState } from "react";
import { Token, TokenAPI } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export default function TokenActions({ token }: { token: Token }) {
  const [isRevoking, setIsRevoking] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [revocationReason, setRevocationReason] = useState<string>("");

  const handleRevoke = async () => {
    if (confirm(`Are you sure you want to revoke this token: ${token.token_id}?`)) {
      setIsRevoking(true);
      try {
        await TokenAPI.revoke(token.token_id, revocationReason || "Manually revoked from admin panel");
        toast.success(`Token ${token.token_id} revoked successfully`);
        window.location.reload();
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to revoke token");
      } finally {
        setIsRevoking(false);
      }
    }
  };

  return (
    <div className="space-x-2">
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">View</Button>
        </DialogTrigger>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Token Details</DialogTitle>
            <DialogDescription>
              Details for token {token.token_id}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <h3 className="font-medium">Basic Information</h3>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="text-sm text-muted-foreground">Token ID:</div>
                <div className="font-mono text-xs">{token.token_id}</div>
                <div className="text-sm text-muted-foreground">Client ID:</div>
                <div className="font-mono text-xs">{token.client_id}</div>
                <div className="text-sm text-muted-foreground">Task ID:</div>
                <div className="font-mono text-xs">{token.task_id || 'N/A'}</div>
                {token.parent_task_id && (
                  <>
                    <div className="text-sm text-muted-foreground">Parent Task ID:</div>
                    <div className="font-mono text-xs">{token.parent_task_id}</div>
                  </>
                )}
                {token.parent_token_id && (
                  <>
                    <div className="text-sm text-muted-foreground">Parent Token ID:</div>
                    <div className="font-mono text-xs">{token.parent_token_id}</div>
                  </>
                )}
                <div className="text-sm text-muted-foreground">Issued At:</div>
                <div>{new Date(token.issued_at).toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Expires At:</div>
                <div>{new Date(token.expires_at).toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Status:</div>
                <div>
                  <Badge 
                    variant={
                      token.is_revoked ? "destructive" : 
                      new Date(token.expires_at) < new Date() ? "secondary" : 
                      "default"
                    }
                  >
                    {token.is_revoked ? "Revoked" : 
                     new Date(token.expires_at) < new Date() ? "Expired" : 
                     "Active"}
                  </Badge>
                </div>
              </div>
            </div>
            
            <Separator />
            
            <div>
              <h3 className="font-medium">Scopes & Permissions</h3>
              <div className="mt-2">
                <div className="text-sm text-muted-foreground mb-1">Authorized Scopes:</div>
                <div className="flex flex-wrap gap-1">
                  {token.scope?.map((s, idx) => (
                    <Badge key={idx} variant="outline">{s}</Badge>
                  )) || <span className="text-muted-foreground">None</span>}
                </div>
                
                <div className="text-sm text-muted-foreground mt-3 mb-1">Granted Tools:</div>
                <div className="flex flex-wrap gap-1">
                  {token.granted_tools?.map((tool, idx) => (
                    <Badge key={idx} variant="outline">{tool}</Badge>
                  )) || <span className="text-muted-foreground">None</span>}
                </div>
                
                <div className="text-sm text-muted-foreground mt-3 mb-1">Granted Resources:</div>
                <div className="flex flex-wrap gap-1">
                  {token.granted_resources?.map((resource, idx) => (
                    <Badge key={idx} variant="outline">{resource}</Badge>
                  )) || <span className="text-muted-foreground">None</span>}
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      <Button
        variant="destructive"
        size="sm"
        onClick={handleRevoke}
        disabled={isRevoking || token.is_revoked}
      >
        {isRevoking ? "Revoking..." : "Revoke"}
      </Button>
    </div>
  );
} 