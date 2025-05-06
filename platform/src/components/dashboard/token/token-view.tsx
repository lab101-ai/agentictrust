"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ShieldOff } from "lucide-react";
import { TokenAPI, type Token } from "@/lib/api";
import { TokenDetailsCard } from "./token-details-card";
import { TokenPermissionsCard } from "./token-permissions-card";
// If your project has an alert-dialog component, uncomment and update the path
// If not, use the dialog component or create an alert-dialog component
import { 
  Dialog,
  DialogContent,
  DialogDescription, 
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog";
import { AlertCircle } from "lucide-react";

interface TokenViewProps {
  id?: string;
  initialToken?: Token;
}

export const TokenView = ({ id, initialToken }: TokenViewProps) => {
  const [token, setToken] = useState<Token | undefined>(initialToken);
  const [isRevoking, setIsRevoking] = useState(false);
  const router = useRouter();

  const handleRevoke = async () => {
    if (!id) return;
    
    try {
      setIsRevoking(true);
      await TokenAPI.revoke(id);
      toast.success("Token revoked successfully");
      
      // Update token state with revoked status
      if (token) {
        setToken({
          ...token,
          is_revoked: true,
          revoked_at: new Date().toISOString()
        });
      }
    } catch (error) {
      toast.error(`Failed to revoke token: ${(error as Error).message}`);
    } finally {
      setIsRevoking(false);
    }
  };

  if (!token) {
    return null;
  }

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button variant="ghost" onClick={() => router.back()} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Token Details</h1>
        </div>
        
        {!token.is_revoked && new Date(token.expires_at) > new Date() && (
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="destructive" disabled={isRevoking}>
                <ShieldOff className="mr-2 h-4 w-4" />
                {isRevoking ? "Revoking..." : "Revoke Token"}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Revoke Token</DialogTitle>
                <DialogDescription>
                  Are you sure you want to revoke this token? This action cannot be undone.
                  Once revoked, the token can no longer be used for authentication.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => document.querySelector('[role="dialog"]')?.dispatchEvent(new CustomEvent('close'))}>Cancel</Button>
                <Button variant="destructive" onClick={handleRevoke}>
                  Revoke Token
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <TokenDetailsCard token={token} />
        <TokenPermissionsCard token={token} />
      </div>
    </div>
  );
};
