"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink, RefreshCcw } from "lucide-react";
import { AuditAPI, type AuditLog } from "@/lib/api";
import { AuditDetailsCard } from "./audit-details-card";
import { AuditTaskCard } from "./audit-task-card";

interface AuditViewProps {
  id?: string;
  initialAudit?: AuditLog;
}

export const AuditView = ({ id, initialAudit }: AuditViewProps) => {
  const [audit, setAudit] = useState<AuditLog | undefined>(initialAudit);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();

  const handleRefresh = async () => {
    if (!id) return;
    
    try {
      setIsRefreshing(true);
      const refreshedAudit = await AuditAPI.get(id);
      setAudit(refreshedAudit);
      toast.success("Audit data refreshed");
    } catch (error) {
      toast.error(`Failed to refresh audit data: ${(error as Error).message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!audit) {
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
          <h1 className="text-3xl font-semibold">Audit Log Details</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2"
          >
            <RefreshCcw className="h-4 w-4" />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
          
          {audit.task_id && (
            <Button
              variant="outline"
              onClick={() => router.push(`/dashboard/audit/chain/${audit.task_id}`)}
              className="flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              View Task Chain
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <AuditDetailsCard audit={audit} />
        <AuditTaskCard audit={audit} />
      </div>
    </div>
  );
};
