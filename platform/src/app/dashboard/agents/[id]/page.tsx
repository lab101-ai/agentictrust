"use client";

import { useEffect, useState, use } from "react";
import { toast } from "sonner";
import { AgentForm } from "@/components/dashboard/agent";
import { AgentAPI, type Agent } from "@/lib/api";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface EditAgentPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function EditAgentPage({ params }: EditAgentPageProps) {
  const { id } = use(params);
  const agentId = id;
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgentData = async () => {
      setLoading(true);
      setError(null);
      try {
        const agentData = await AgentAPI.get(agentId);
        setAgent(agentData);
      } catch (err) {
        console.error("Failed to fetch agent:", err);
        setError("Failed to load agent data. Please try again.");
        toast.error("Failed to load agent data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgentData();
  }, [agentId]);

  if (loading) {
    return (
      <div className="container py-6">
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-t-2 border-primary rounded-full mx-auto mb-4"></div>
            <p>Loading agent data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="container py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || "Failed to load agent data. Please try again."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <AgentForm id={agentId} initialAgent={agent} />;
}
