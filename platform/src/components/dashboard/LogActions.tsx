"use client";

import { useState } from "react";
import { AuditLog, AuditAPI } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

export default function LogActions({ log }: { log: AuditLog }) {
  const [isLoadingChain, setIsLoadingChain] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showTaskChain, setShowTaskChain] = useState(false);
  const [taskChain, setTaskChain] = useState<any>(null);

  const handleViewTaskChain = async () => {
    if (!log.task_id) return;
    
    setIsLoadingChain(true);
    setShowTaskChain(true);
    
    try {
      const chain = await AuditAPI.getTaskChain(log.task_id);
      setTaskChain(chain);
    } catch (error) {
      // Error handled by toast
      toast.error("Failed to load task chain");
    } finally {
      setIsLoadingChain(false);
    }
  };

  return (
    <div className="space-x-2">
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">Details</Button>
        </DialogTrigger>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Log Details</DialogTitle>
            <DialogDescription>
              Details for log {log.log_id}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <h3 className="font-medium">Basic Information</h3>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="text-sm text-muted-foreground">Timestamp:</div>
                <div>{new Date(log.timestamp).toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Client ID:</div>
                <div className="font-mono text-xs">{log.client_id}</div>
                <div className="text-sm text-muted-foreground">Token ID:</div>
                <div className="font-mono text-xs">{log.token_id || 'N/A'}</div>
                {log.task_id && (
                  <>
                    <div className="text-sm text-muted-foreground">Task ID:</div>
                    <div className="font-mono text-xs">{log.task_id}</div>
                  </>
                )}
                {log.parent_task_id && (
                  <>
                    <div className="text-sm text-muted-foreground">Parent Task ID:</div>
                    <div className="font-mono text-xs">{log.parent_task_id}</div>
                  </>
                )}
                <div className="text-sm text-muted-foreground">Event Type:</div>
                <div>{log.event_type}</div>
                <div className="text-sm text-muted-foreground">Status:</div>
                <div>
                  <Badge 
                    variant={
                      log.status === "success" ? "default" : 
                      log.status === "failed" ? "destructive" : 
                      "secondary"
                    }
                  >
                    {log.status}
                  </Badge>
                </div>
              </div>
            </div>
            
            {log.details && (
              <div>
                <h3 className="font-medium">Additional Details</h3>
                <pre className="bg-muted p-4 rounded-md mt-2 overflow-auto text-sm">
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
      
      <Dialog open={showTaskChain} onOpenChange={setShowTaskChain}>
        <DialogTrigger asChild>
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={handleViewTaskChain}
            disabled={isLoadingChain || !log.task_id}
          >
            {isLoadingChain ? "Loading..." : "Task Chain"}
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-5xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Task Chain Visualization</DialogTitle>
            <DialogDescription>
              Showing relationship between parent and child tasks for {log.task_id}
            </DialogDescription>
          </DialogHeader>
          
          {isLoadingChain ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
            </div>
          ) : taskChain ? (
            <div className="space-y-4 mt-4">
              <div className="border rounded-md p-4">
                <h3 className="font-medium mb-2">Task Chain</h3>
                <div className="space-y-2">
                  {taskChain.task_chain.map((taskId: string, idx: number) => (
                    <div key={taskId} className="flex items-center">
                      {idx > 0 && (
                        <div className="h-6 border-l-2 border-dotted mx-4"></div>
                      )}
                      <Badge variant={idx === 0 ? "default" : "outline"} className="font-mono text-xs">
                        {taskId} {idx === 0 ? "(Root)" : ""}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="border rounded-md p-4">
                <h3 className="font-medium mb-2">Task Details</h3>
                <div className="space-y-4">
                  {taskChain.task_details.map((task: any) => (
                    <div key={task.task_id} className="border-b pb-2 last:border-b-0">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="text-sm text-muted-foreground">Task ID:</div>
                        <div className="font-mono text-xs">{task.task_id}</div>
                        <div className="text-sm text-muted-foreground">Event Type:</div>
                        <div>{task.event_type}</div>
                        <div className="text-sm text-muted-foreground">Status:</div>
                        <div>
                          <Badge 
                            variant={
                              task.status === "success" ? "default" : 
                              task.status === "failed" ? "destructive" : 
                              "secondary"
                            }
                          >
                            {task.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">Timestamp:</div>
                        <div>{new Date(task.timestamp).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center p-8 text-muted-foreground">
              No task chain data available
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
} 