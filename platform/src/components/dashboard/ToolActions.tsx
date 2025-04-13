"use client";

import { Button } from "@/components/ui/button";
import { Tool, ToolAPI } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { ViewToolDialog } from "@/components/dashboard/ViewToolDialog";
import { EditToolDialog } from "@/components/dashboard/EditToolDialog";

interface ToolActionsProps {
  tool: Tool;
}

export default function ToolActions({ tool }: ToolActionsProps) {
  const [isActivating, setIsActivating] = useState(false);
  const [isDeactivating, setIsDeactivating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const handleActivate = async () => {
    setIsActivating(true);
    try {
      await ToolAPI.activate(tool.tool_id);
      toast.success(`Tool ${tool.name} activated successfully`);
      // Refresh the page to get updated data
      window.location.reload();
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to activate tool");
    } finally {
      setIsActivating(false);
    }
  };

  const handleDeactivate = async () => {
    setIsDeactivating(true);
    try {
      await ToolAPI.deactivate(tool.tool_id);
      toast.success(`Tool ${tool.name} deactivated successfully`);
      // Refresh the page to get updated data
      window.location.reload();
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to deactivate tool");
    } finally {
      setIsDeactivating(false);
    }
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete this tool: ${tool.name}?`)) {
      setIsDeleting(true);
      try {
        await ToolAPI.delete(tool.tool_id);
        toast.success(`Tool ${tool.name} deleted successfully`);
        // Refresh the page to get updated data
        window.location.reload();
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to delete tool");
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <div className="space-x-2">
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => setViewDialogOpen(true)}
      >
        View
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => setEditDialogOpen(true)}
      >
        Edit
      </Button>
      <Button 
        variant="destructive" 
        size="sm"
        onClick={handleDelete}
        disabled={isDeleting}
      >
        {isDeleting ? "Deleting..." : "Delete"}
      </Button>
      
      {tool.is_active ? (
        <Button 
          variant="secondary" 
          size="sm"
          onClick={handleDeactivate}
          disabled={isDeactivating}
        >
          {isDeactivating ? "Deactivating..." : "Deactivate"}
        </Button>
      ) : (
        <Button 
          variant="default" 
          size="sm"
          onClick={handleActivate}
          disabled={isActivating}
        >
          {isActivating ? "Activating..." : "Activate"}
        </Button>
      )}
      
      <ViewToolDialog 
        tool={tool} 
        open={viewDialogOpen} 
        onOpenChange={setViewDialogOpen} 
      />
      
      <EditToolDialog 
        tool={tool} 
        open={editDialogOpen} 
        onOpenChange={setEditDialogOpen} 
      />
    </div>
  );
} 