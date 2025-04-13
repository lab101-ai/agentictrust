"use client";

import { useState, useEffect } from "react";
import { AuditLog, AuditAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import LogActions from "@/components/dashboard/LogActions";

// Helper function to format event types for display
function formatEventType(eventType: string): string {
  return eventType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function AuditTab() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await AuditAPI.getAll();
      setLogs(data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <Card id="audit-logs">
      <CardHeader>
        <CardTitle>Audit Logs</CardTitle>
        <CardDescription>View system activity and security events</CardDescription>
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading audit logs</AlertTitle>
            <AlertDescription>There was a problem fetching the logs data.</AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`log-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            {logs.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Task ID</TableHead>
                    <TableHead>Parent Task</TableHead>
                    <TableHead>Event Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.log_id}>
                      <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                      <TableCell className="font-mono text-xs">{log.client_id.substring(0, 8)}...</TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.task_id ? log.task_id.substring(0, 8) + '...' : 'N/A'}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.parent_task_id ? log.parent_task_id.substring(0, 8) + '...' : 'N/A'}
                      </TableCell>
                      <TableCell>{formatEventType(log.event_type)}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            log.status === "success" ? "default" : 
                            log.status === "failed" ? "destructive" : 
                            "secondary"
                          }
                        >
                          {log.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <LogActions log={log} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No audit logs available.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
