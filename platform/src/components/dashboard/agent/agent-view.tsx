"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Pencil, Trash2, Check } from "lucide-react";
import { AgentAPI, type Agent } from "@/lib/api";
import { AgentDetailsCard } from "./agent-details-card";
import { AgentPermissionsCard } from "./agent-permissions-card";
import { 
  Dialog,
  DialogContent,
  DialogDescription, 
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog";
import { AlertCircle } from "lucide-react";

interface AgentViewProps {
  id?: string;
  initialAgent?: Agent;
}

export const AgentView = ({ id, initialAgent }: AgentViewProps) => {
  const [agent, setAgent] = useState<Agent | undefined>(initialAgent);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isActivating, setIsActivating] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    if (!id) return;
    
    try {
      setIsDeleting(true);
      await AgentAPI.delete(id);
      toast.success("Agent deleted successfully");
      router.push("/dashboard?tab=agents");
    } catch (error) {
      toast.error(`Failed to delete agent: ${(error as Error).message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleActivationToggle = async () => {
    if (!id || !agent) return;
    
    try {
      setIsActivating(true);
      if (agent.is_active) {
        // Update agent with is_active set to false since there's no dedicated deactivate method
        // Need to cast to any since AgentRegistration doesn't include is_active
        const updatedAgent = await AgentAPI.update(id, { is_active: false } as any);
        toast.success("Agent deactivated successfully");
        
        setAgent(updatedAgent);
      } else {
        // For activation, if there's a registration token, we can use activate method
        // Otherwise, update with is_active: true
        if (agent.registration_token) {
          const activatedAgent = await AgentAPI.activate(agent.registration_token);
          setAgent(activatedAgent);
        } else {
          // Need to cast to any since AgentRegistration doesn't include is_active
          const updatedAgent = await AgentAPI.update(id, { is_active: true } as any);
          setAgent(updatedAgent);
        }
        toast.success("Agent activated successfully");
      }
    } catch (error) {
      toast.error(`Failed to update agent status: ${(error as Error).message}`);
    } finally {
      setIsActivating(false);
    }
  };

  if (!agent) {
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
          <h1 className="text-3xl font-semibold">Agent Details</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/dashboard/agents/${id}/edit`)}
            className="flex items-center gap-2"
          >
            <Pencil className="h-4 w-4" />
            Edit
          </Button>
          
          <Button
            variant={agent.is_active ? "destructive" : "default"}
            onClick={handleActivationToggle}
            disabled={isActivating}
            className="flex items-center gap-2"
          >
            <Check className="h-4 w-4" />
            {isActivating 
              ? (agent.is_active ? "Deactivating..." : "Activating...") 
              : (agent.is_active ? "Deactivate" : "Activate")
            }
          </Button>
          
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="destructive" disabled={isDeleting}>
                <Trash2 className="mr-2 h-4 w-4" />
                {isDeleting ? "Deleting..." : "Delete Agent"}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete Agent</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete this agent? This action cannot be undone.
                  All related tokens and tasks will remain but will no longer be associated with this agent.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => document.querySelector('[role="dialog"]')?.dispatchEvent(new CustomEvent('close'))}>Cancel</Button>
                <Button variant="destructive" onClick={handleDelete}>
                  Delete Agent
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <AgentDetailsCard agent={agent} />
        <AgentPermissionsCard agent={agent} />
      </div>
    </div>
  );
};
