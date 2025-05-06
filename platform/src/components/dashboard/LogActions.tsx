"use client";

import { AuditLog } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { FileText, Share2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LogActions({ log }: { log: AuditLog }) {
  const router = useRouter();
  
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => router.push(`/dashboard/audit/${log.log_id}`)}
        title="View log details"
      >
        <FileText className="h-4 w-4" />
        <span className="sr-only">Details</span>
      </Button>
      
      {log.task_id && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-blue-600 bg-blue-50 hover:text-blue-700 hover:bg-blue-100"
          onClick={() => router.push(`/dashboard/audit/chain/${log.task_id}`)}
          disabled={!log.task_id}
          title="View task chain"
        >
          <Share2 className="h-4 w-4" />
          <span className="sr-only">Task Chain</span>
        </Button>
      )}
    </div>
  );
}