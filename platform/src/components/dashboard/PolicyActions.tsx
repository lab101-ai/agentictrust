import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Play, PauseCircle, Trash2, Pencil } from "lucide-react";
import { toast } from "sonner";
import { PolicyAPI, type Policy } from "@/lib/api";

interface PolicyActionsProps {
  policy: Policy;
  onDelete: (policyId: string) => void;
  onEdit: (policy: Policy) => void;

  onRefresh: () => void;
}

export const PolicyActions = ({
  policy,
  onDelete,
  onEdit,
  onRefresh
}: PolicyActionsProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleToggleActive = async () => {
    try {
      setIsLoading(true);
      if (policy.is_active) {
        await PolicyAPI.deactivate(policy.policy_id);
        toast.success(`Policy "${policy.name}" deactivated`);
      } else {
        await PolicyAPI.activate(policy.policy_id);
        toast.success(`Policy "${policy.name}" activated`);
      }
      onRefresh();
    } catch (error) {
      toast.error(`Failed to ${policy.is_active ? 'deactivate' : 'activate'} policy: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete policy "${policy.name}"?`)) {
      try {
        setIsLoading(true);
        await PolicyAPI.delete(policy.policy_id);
        toast.success(`Policy "${policy.name}" deleted`);
        onDelete(policy.policy_id);
      } catch (error) {
        toast.error(`Failed to delete policy: ${(error as Error).message}`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="flex items-center justify-end gap-2">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => onEdit(policy)}
        title="Edit policy"
        disabled={isLoading}
      >
        <Pencil className="h-4 w-4" />
        <span className="sr-only">Edit</span>
      </Button>
      
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={handleToggleActive}
        title={policy.is_active ? "Deactivate policy" : "Activate policy"}
        disabled={isLoading}
      >
        {policy.is_active ? (
          <PauseCircle className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        <span className="sr-only">{policy.is_active ? "Deactivate" : "Activate"}</span>
      </Button>
      
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-destructive bg-destructive/10 hover:text-destructive hover:bg-destructive/20"
        onClick={handleDelete}
        title="Delete policy"
        disabled={isLoading}
      >
        <Trash2 className="h-4 w-4" />
        <span className="sr-only">Delete</span>
      </Button>
    </div>
  );
};
