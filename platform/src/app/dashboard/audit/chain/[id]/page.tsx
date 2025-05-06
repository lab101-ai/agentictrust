"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { AuditAPI } from "@/lib/api";
import { toast } from "sonner";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AuditChainView } from "@/components/dashboard/audit/audit-chain-view";

interface ViewTaskChainPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function ViewTaskChainPage({ params }: ViewTaskChainPageProps) {
  const { id } = use(params);
  const taskId = id;
  const router = useRouter();
  
  const [taskChain, setTaskChain] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper to transform nested task details (array of logs) to summary objects expected by UI
  const transformTaskDetails = (rawDetails: any[]): any[] => {
    if (!Array.isArray(rawDetails)) return [];
    return rawDetails
      .map((taskLogs: any) => {
        // Each taskLogs should be an array of log objects for a single task
        if (!Array.isArray(taskLogs) || taskLogs.length === 0) return null;

        // Prefer the first log of type 'task' as the primary summary; fallback to first element
        const summaryLog = taskLogs.find((l: any) => l.type === "task") || taskLogs[0];

        // Keep the log 'type' for UI differentiation
        return {
          ...summaryLog,
          event_count: taskLogs.length,
          events: taskLogs,
        };
      })
      .filter(Boolean);
  };

  // Fetch task chain data
  useEffect(() => {
    const fetchTaskChainData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Add delay to ensure console logs are visible
        console.log('Fetching task chain for task ID:', taskId);
        
        const response = await AuditAPI.getTaskChain(taskId);
        
        // Log the response to help diagnose the issue
        console.log('Task chain API response:', response);
        
        // Check if response has expected structure
        if (response) {
          const transformedDetails = transformTaskDetails(response.task_details || []);
          // Create standardized structure if properties are missing
          const standardizedResponse = {
            task_chain: response.task_chain || [],
            task_details: transformedDetails,
            root_task_id: response.root_task_id || taskId
          };
          
          console.log('Using standardized response:', standardizedResponse);
          setTaskChain(standardizedResponse);
        } else {
          // Handle unexpected response format
          console.error('Unexpected API response format - got null/undefined');
          setError('Unexpected data format received from server');
          toast.error('Unable to display task chain due to data format issues');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        console.error("Failed to fetch task chain:", errorMessage);
        setError(`Failed to load task chain data: ${errorMessage}`);
        toast.error("Failed to load task chain data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchTaskChainData();
  }, [taskId]);
  
  const handleBack = () => {
    router.push("/dashboard?tab=audit");
  };

  if (loading) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Audit Logs
          </Button>
        </div>
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-t-2 border-primary rounded-full mx-auto mb-4"></div>
            <p>Loading task chain data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !taskChain) {
    return (
      <div className="container py-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Audit Logs
          </Button>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || "Failed to load task chain data. Please try again."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await AuditAPI.getTaskChain(taskId);
      if (response) {
        const transformedDetails = transformTaskDetails(response.task_details || []);
        const standardizedResponse = {
          task_chain: response.task_chain || [],
          task_details: transformedDetails,
          root_task_id: response.root_task_id || taskId
        };
        
        setTaskChain(standardizedResponse);
      } else {
        setError('Unexpected data format received from server');
        toast.error('Unable to display task chain due to data format issues');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to load task chain data: ${errorMessage}`);
      toast.error("Failed to refresh task chain data");
    } finally {
      setLoading(false);
    }
  };

  return <AuditChainView id={taskId} taskChain={taskChain} onRefresh={handleRefresh} />;
}
