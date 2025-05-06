"use client";

import { Button } from "@/components/ui/button";
import { Tool, ToolAPI } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, Pencil, Trash2 } from "lucide-react";

interface ToolActionsProps {
  tool: Tool;
  onUpdate?: () => void;
}

export default function ToolActions({ tool, onUpdate }: ToolActionsProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete this tool: ${tool.name}?`)) {
      setIsDeleting(true);
      try {
        await ToolAPI.delete(tool.tool_id);
        toast.success(`Tool ${tool.name} deleted successfully`);
        if (onUpdate) {
          onUpdate();
        } else {
          // Refresh the page to get updated data
          window.location.reload();
        }
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to delete tool");
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => router.push(`/dashboard/tools/${tool.tool_id}`)}
        title="Edit tool"
      >
        <Pencil className="h-4 w-4" />
        <span className="sr-only">Edit</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-destructive bg-destructive/10 hover:text-destructive hover:bg-destructive/20"
        onClick={handleDelete}
        disabled={isDeleting}
        title="Delete tool"
      >
        <Trash2 className="h-4 w-4" />
        <span className="sr-only">{isDeleting ? "Deleting..." : "Delete"}</span>
      </Button>
    </div>
  );
}