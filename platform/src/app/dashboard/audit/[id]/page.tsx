"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { AuditAPI, type AuditLog } from "@/lib/api";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AuditView } from "@/components/dashboard/audit/audit-view";

interface ViewAuditLogPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function ViewAuditLogPage({ params }: ViewAuditLogPageProps) {
  const { id } = use(params);
  const logId = id;
  const router = useRouter();
  
  const [log, setLog] = useState<AuditLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch log data
  useEffect(() => {
    const fetchLogData = async () => {
      setLoading(true);
      setError(null);
      try {
        // For our purposes, we'll search using client_id param (which is mandatory for the API)
        // and then filter by log_id on the client side
        const logs = await AuditAPI.getAll(100);
        const filteredLogs = logs.filter(l => l.log_id === logId);
        
        if (filteredLogs && filteredLogs.length > 0) {
          setLog(filteredLogs[0]);
        } else {
          setError("Audit log not found");
          toast.error("Audit log not found");
        }
      } catch (err) {
        console.error("Failed to fetch audit log:", err);
        setError("Failed to load audit log data. Please try again.");
        toast.error("Failed to load audit log data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchLogData();
  }, [logId]);

  if (loading) {
    return (
      <div className="container py-6">
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-t-2 border-primary rounded-full mx-auto mb-4"></div>
            <p>Loading audit log data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !log) {
    return (
      <div className="container py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || "Failed to load audit log data. Please try again."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <AuditView id={logId} initialAudit={log} />;
}
