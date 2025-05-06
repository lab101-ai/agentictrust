"use client";

import { CardContent, Card, CardHeader, CardTitle } from "@/components/ui/card";
import { type AuditLog } from "@/lib/api";
import { IconBadge, StatusBadge } from "@/components/ui/icon-badge";
import { Clock, Server, Info, Hash, UserRound, Key } from "lucide-react";

interface AuditDetailsCardProps {
  audit: AuditLog;
}

export const AuditDetailsCard = ({ audit }: AuditDetailsCardProps) => {
  // Format the timestamp for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Determine status badge color based on status
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "success":
        return <StatusBadge subtype="success">{status}</StatusBadge>;
      case "error":
        return <StatusBadge subtype="error">{status}</StatusBadge>;
      case "warning":
        return <StatusBadge subtype="warning">{status}</StatusBadge>;
      case "pending":
        return <StatusBadge subtype="pending">{status}</StatusBadge>;
      default:
        return <StatusBadge subtype="info">{status}</StatusBadge>;
    }
  };

  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle>Audit Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <Hash className="h-4 w-4 mr-2 text-muted-foreground" />
            Log ID
          </p>
          <p className="text-sm break-all">{audit.log_id}</p>
        </div>
        
        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <Clock className="h-4 w-4 mr-2 text-muted-foreground" />
            Timestamp
          </p>
          <p className="text-sm break-all">{formatDate(audit.timestamp)}</p>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <UserRound className="h-4 w-4 mr-2 text-muted-foreground" />
            Client ID
          </p>
          <p className="text-sm break-all">{audit.client_id}</p>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <Key className="h-4 w-4 mr-2 text-muted-foreground" />
            Token ID
          </p>
          <p className="text-sm break-all">{audit.token_id}</p>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <Server className="h-4 w-4 mr-2 text-muted-foreground" />
            Source IP
          </p>
          <p className="text-sm break-all">{audit.source_ip || "N/A"}</p>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium">Event Type</p>
          <div>
            <IconBadge type="status" subtype="info" icon={Info}>{audit.event_type}</IconBadge>
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium">Status</p>
          <div>
            {getStatusBadge(audit.status)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
