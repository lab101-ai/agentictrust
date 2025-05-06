"use client";

import { CardContent, Card, CardHeader, CardTitle } from "@/components/ui/card";
import { type AuditLog } from "@/lib/api";
import { Link2, GitBranch, LogIn, AlertTriangle } from "lucide-react";
import { IconBadge } from "@/components/ui/icon-badge";
import Link from "next/link";

interface AuditTaskCardProps {
  audit: AuditLog;
}

export const AuditTaskCard = ({ audit }: AuditTaskCardProps) => {
  // Check if the audit contains an error log
  const isErrorLog = audit.details && audit.details._error_log === true;

  // Format JSON details for display
  const formatDetails = (details: any) => {
    if (!details) return "No details";
    
    // Create a copy without internal fields
    const displayDetails = { ...details };
    if (displayDetails._error_log) delete displayDetails._error_log;
    if (displayDetails._error_token_id) delete displayDetails._error_token_id;
    
    // Check if there are any remaining details
    if (Object.keys(displayDetails).length === 0) {
      return "No additional details";
    }
    
    return JSON.stringify(displayDetails, null, 2);
  };

  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle>Task Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isErrorLog && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-md mb-4 flex items-start">
            <AlertTriangle className="h-5 w-5 text-amber-500 mr-2 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-700">Error Log Entry</p>
              <p className="text-sm text-amber-600">
                This is an error log entry created before a token was properly established.
              </p>
            </div>
          </div>
        )}

        <div className="space-y-1">
          <p className="text-sm font-medium flex items-center">
            <LogIn className="h-4 w-4 mr-2 text-muted-foreground" />
            Task ID
          </p>
          <Link 
            href={`/dashboard/audit/view/${audit.task_id}`} 
            className="text-sm text-primary hover:underline break-all"
          >
            {audit.task_id}
          </Link>
        </div>
        
        {audit.parent_task_id && (
          <div className="space-y-1">
            <p className="text-sm font-medium flex items-center">
              <GitBranch className="h-4 w-4 mr-2 text-muted-foreground" />
              Parent Task ID
            </p>
            <Link 
              href={`/dashboard/audit/view/${audit.parent_task_id}`}
              className="text-sm text-primary hover:underline break-all"
            >
              {audit.parent_task_id}
            </Link>
          </div>
        )}

        {audit.task_id && (
          <div className="space-y-1">
            <p className="text-sm font-medium flex items-center">
              <Link2 className="h-4 w-4 mr-2 text-muted-foreground" />
              Task Chain
            </p>
            <Link
              href={`/dashboard/audit/chain/${audit.task_id}`}
              className="text-sm inline-flex items-center text-primary hover:underline"
            >
              View Task Chain
              <svg className="ml-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        )}

        <div className="space-y-1">
          <p className="text-sm font-medium">Details</p>
          <div className="mt-2 border rounded-md p-3 bg-gray-50">
            <pre className="text-xs whitespace-pre-wrap break-all">{formatDetails(audit.details)}</pre>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
