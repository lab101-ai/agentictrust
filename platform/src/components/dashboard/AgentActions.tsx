"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Agent, AgentAPI } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Trash2, Check } from "lucide-react";

interface AgentActionsProps {
  agent: Agent;
  onUpdate?: () => Promise<void> | void;
}

export default function AgentActions({ agent, onUpdate }: AgentActionsProps) {
  const router = useRouter();
  const [isActivating, setIsActivating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleActivate = async () => {
    if (!agent.registration_token) {
      toast.error("No registration token available for this agent");
      return;
    }
    
    setIsActivating(true);
    try {
      await AgentAPI.activate(agent.registration_token);
      toast.success(`Agent ${agent.agent_name} activated successfully`);
      // Call the onUpdate callback if provided
      if (onUpdate) {
        await onUpdate();
      }
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to activate agent");
    } finally {
      setIsActivating(false);
    }
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete this agent: ${agent.agent_name}?`)) {
      setIsDeleting(true);
      try {
        await AgentAPI.delete(agent.client_id);
        toast.success(`Agent ${agent.agent_name} deleted successfully`);
        // Call the onUpdate callback if provided
        if (onUpdate) {
          await onUpdate();
        }
      } catch (error) {
        // Error handled by toast
        toast.error("Failed to delete agent");
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
        onClick={() => router.push(`/dashboard/agents/${agent.client_id}`)}
        title="Edit agent"
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
        title="Delete agent"
      >
        <Trash2 className="h-4 w-4" />
        <span className="sr-only">{isDeleting ? "Deleting..." : "Delete"}</span>
      </Button>
      
      {!agent.is_active && agent.registration_token && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-emerald-600 bg-emerald-50 hover:text-emerald-700 hover:bg-emerald-100"
          onClick={handleActivate}
          disabled={isActivating}
          title="Activate agent"
        >
          <Check className="h-4 w-4" />
          <span className="sr-only">{isActivating ? "Activating..." : "Activate"}</span>
        </Button>
      )}
    </div>
  );
} 