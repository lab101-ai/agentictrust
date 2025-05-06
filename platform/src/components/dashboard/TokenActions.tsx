"use client";

import { Token } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ShieldOff } from "lucide-react";
import { useRouter } from "next/navigation";

interface TokenActionsProps {
  token: Token;
}

export default function TokenActions({ token }: TokenActionsProps) {
  const router = useRouter();
  
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="icon"
        className={`h-8 w-8 ${token.is_revoked ? 'bg-destructive/10 text-destructive/50 cursor-not-allowed' : 'text-destructive hover:text-destructive hover:bg-destructive/10'}`}
        disabled={token.is_revoked}
        title={token.is_revoked ? "Token already revoked" : "Revoke token"}
        onClick={() => {
          if (!token.is_revoked) {
            router.push(`/dashboard/tokens/revoke/${token.token_id}`);
          }
        }}
      >
        <ShieldOff className="h-4 w-4" />
        <span className="sr-only">Revoke</span>
      </Button>
    </div>
  );
}