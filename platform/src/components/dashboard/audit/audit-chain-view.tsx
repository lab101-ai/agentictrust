"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Share2, AlertCircle, ExternalLink, RefreshCcw, ChevronDown, ChevronRight, GitBranch, FileText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { IconBadge, StatusBadge } from "@/components/ui/icon-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { AuditLog } from "@/lib/api";

interface TaskDetail {
  task_id: string;
  parent_task_id?: string;
  client_id: string;
  token_id?: string;
  event_type?: string;
  status?: string;
  timestamp?: string;
  details?: any;
  event_count?: number;
  log_id?: string;
  events?: AuditLog[];
}

interface AuditChainViewProps {
  id?: string;
  taskChain: {
    task_chain: string[];
    task_details: TaskDetail[];
    root_task_id: string;
  };
  onRefresh?: () => Promise<void>;
}

export const AuditChainView = ({ id, taskChain, onRefresh }: AuditChainViewProps) => {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set([]));
  
  // Build a map of tasks with their children for improved display
  const taskHierarchy = useMemo(() => {
    const hierarchy: Record<string, string[]> = {};
    
    // Initialize an empty array for each task ID
    if (taskChain.task_chain) {
      taskChain.task_chain.forEach(taskId => {
        hierarchy[taskId] = [];
      });
      
      // Populate children arrays
      if (taskChain.task_details) {
        taskChain.task_details.forEach(task => {
          if (task.parent_task_id && hierarchy[task.parent_task_id]) {
            hierarchy[task.parent_task_id].push(task.task_id);
          }
        });
      }
    }
    
    return hierarchy;
  }, [taskChain]);
  
  // Get task details by ID for quick lookup
  const taskDetailsMap = useMemo(() => {
    const detailsMap: Record<string, TaskDetail> = {};
    
    if (taskChain.task_details) {
      taskChain.task_details.forEach(task => {
        detailsMap[task.task_id] = task;
      });
    }
    
    return detailsMap;
  }, [taskChain.task_details]);
  
  const toggleTaskExpand = (taskId: string) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };
  
  const handleBack = () => {
    router.back();
  };
  
  const handleRefresh = async () => {
    if (!onRefresh) return;
    
    try {
      setIsRefreshing(true);
      await onRefresh();
      toast.success("Task chain data refreshed");
    } catch (error) {
      toast.error(`Failed to refresh task chain data: ${(error as Error).message}`);
    } finally {
      setIsRefreshing(false);
    }
  };
  
  // Format event type for better display
  const formatEventType = (eventType: string) => {
    if (!eventType) return 'Unknown';
    return eventType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };
  
  // Build a human-readable title for any log entry based on its type
  const formatEventTitle = (evt: any): string => {
    if (!evt) return 'Unknown';
    switch (evt.type) {
      case 'task':
        return formatEventType(evt.event_type || evt.status || 'Task');
      case 'policy':
        return formatEventType(evt.action || 'Policy');
      case 'scope':
        return formatEventType(evt.action || 'Scope');
      case 'token':
        return formatEventType(evt.event_type ? `Token ${evt.event_type}` : 'Token');
      default:
        return 'Unknown';
    }
  };
  
  // Derive display status text from different log types
  const getEventStatus = (evt: any): string | undefined => {
    if (!evt) return undefined;
    return (
      evt.status || // task logs
      evt.decision || // policy logs
      evt.action || // scope logs
      evt.event_type // token logs (issued / revoked / refreshed)
    );
  };
  
  // Map status text to badge subtype
  const getBadgeSubtype = (status?: string): "success" | "error" | "pending" => {
    if (!status) return "pending";
    const normalized = status.toLowerCase();
    if ([
      "success",
      "allowed",
      "granted",
      "issued",
      "completed",
      "refreshed",
    ].includes(normalized)) {
      return "success";
    }
    if (["error", "failed", "denied", "revoked"].includes(normalized)) {
      return "error";
    }
    return "pending";
  };
  
  // Renders a task node in the hierarchical view
  const renderTaskNode = (taskId: string, depth = 0, isLastChild = true) => {
    const task = taskDetailsMap[taskId];
    const hasChildren = taskHierarchy[taskId]?.length > 0;
    const isExpanded = expandedTasks.has(taskId);
    
    if (!task) return null;
    
    // Determine appropriate badge type based on position in hierarchy
    const getBadgeType = () => {
      if (taskId === taskChain.root_task_id) return { type: "resource" as const, subtype: "database" };
      if (depth === 1) return { type: "tool" as const, subtype: "utility" };
      return { type: "time" as const, subtype: "scheduled" };
    };
    
    const { type, subtype } = getBadgeType();
    
    return (
      <div key={taskId} className="mb-1">
        <div className="flex items-start">
          <div className="flex items-center mr-2" style={{ paddingLeft: `${depth * 20}px` }}>
            {depth > 0 && (
              <div 
                className={`border-l-2 border-dashed h-6 absolute`} 
                style={{ left: `${depth * 20 - 16}px` }}
              />
            )}
            
            {hasChildren ? (
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-6 w-6 p-0 mr-1" 
                onClick={() => toggleTaskExpand(taskId)}
                aria-label={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            ) : (
              <div className="w-7" />
            )}
          </div>
          
          <div className="flex flex-col flex-1">
            <div className="flex items-center">
              <IconBadge type={type} subtype={subtype} className="mr-2 text-xs">
                {taskId === taskChain.root_task_id ? "Root" : formatEventTitle(task)}
              </IconBadge>
              
              <span className="font-mono text-xs opacity-70">{taskId.substring(0, 8)}...</span>
              
              {(
                (() => {
                  const s = getEventStatus(task);
                  if (!s) return null;
                  return (
                    <div className="ml-2">
                      <StatusBadge subtype={getBadgeSubtype(s)}>{s}</StatusBadge>
                    </div>
                  );
                })()
              )}
              
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 ml-auto"
                onClick={() => router.push(`/dashboard/audit/${task.log_id || task.task_id}`)}
                title="View task details"
              >
                <FileText className="h-3 w-3" />
              </Button>
            </div>
            
            {isExpanded && task.details && (
              <div>
                <div className="mt-2 ml-8 p-3 border rounded-md bg-muted text-xs overflow-auto">
                  <pre className="whitespace-pre-wrap break-all">
                    {JSON.stringify(task.details, null, 2)}
                  </pre>
                </div>
                
                {/* Show events if available */}
                {task.events && task.events.length > 1 && (
                  <div className="mt-2 ml-8">
                    <div className="text-xs font-medium mb-1">All Events ({task.events.length}):</div>
                    <div className="border rounded-md divide-y">
                      {task.events.map((event, index) => (
                        <div key={event.log_id || index} className="p-2 text-xs hover:bg-muted">
                          <div className="flex justify-between mb-1">
                            <span className="font-medium">{formatEventTitle(event)}</span>
                            <span className="text-muted-foreground">
                              {event.timestamp ? new Date(event.timestamp).toLocaleString() : ''}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            {(() => {
                              const s = getEventStatus(event);
                              return (
                                <StatusBadge subtype={getBadgeSubtype(s)} className="text-xs">
                                  {s}
                                </StatusBadge>
                              );
                            })()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        {/* Render children recursively if expanded */}
        {isExpanded && hasChildren && (
          <div className="relative">
            {taskHierarchy[taskId].map((childTaskId, index, arr) => (
              renderTaskNode(childTaskId, depth + 1, index === arr.length - 1)
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button variant="ghost" onClick={handleBack} className="mr-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-semibold">Task Chain</h1>
        </div>
        
        <div className="flex items-center gap-2">
          {onRefresh && (
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2"
            >
              <RefreshCcw className="h-4 w-4" />
              {isRefreshing ? "Refreshing..." : "Refresh"}
            </Button>
          )}
        </div>
      </div>
      
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              <CardTitle>Task Chain</CardTitle>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                // Toggle expand all tasks
                if (expandedTasks.size > 0) {
                  setExpandedTasks(new Set());
                } else {
                  setExpandedTasks(new Set(taskChain.task_chain));
                }
              }}
            >
              {expandedTasks.size > 0 ? "Collapse All" : "Expand All"}
            </Button>
          </div>
          <CardDescription>
            Viewing task chain starting from {taskChain.root_task_id}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="space-y-6">
            {/* Hierarchy section */}
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Task Chain Hierarchy
              </h3>
              
              {taskChain.task_chain && taskChain.task_chain.length > 0 ? (
                <div className="relative space-y-1 border rounded-md p-4">
                  {/* Only render the root task and let the recursion handle the rest */}
                  {renderTaskNode(taskChain.root_task_id)}
                </div>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>No Data Available</AlertTitle>
                  <AlertDescription>
                    No task chain data available. The task may be isolated or data format is unexpected.
                  </AlertDescription>
                </Alert>
              )}
            </div>
            
            <Separator />
            
            {/* Task details section */}
            <div>
              <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Task Details
              </h3>
              
              <div className="space-y-4">
          {taskChain.task_details && Array.isArray(taskChain.task_details) && taskChain.task_details.length > 0 ? (
            taskChain.task_details.map((task) => (
              <div key={task.task_id} className="border rounded-md overflow-hidden">
                <div className="border-b p-3 bg-muted/30">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <IconBadge 
                        type={task.task_id === taskChain.root_task_id ? "resource" as const : "tool" as const}
                        subtype={task.task_id === taskChain.root_task_id ? "database" : "utility"}
                      >
                        {task.task_id === taskChain.root_task_id ? "Root Task" : "Child Task"}
                      </IconBadge>
                      <CardTitle className="text-base">
                        {task.task_id === taskChain.root_task_id
                          ? (task.event_type ? formatEventTitle(task) : 'Root Task')
                          : formatEventTitle(task)}
                      </CardTitle>
                    </div>
                    {(() => {
                      const s = getEventStatus(task);
                      if (!s) return null;
                      return (
                        <StatusBadge subtype={getBadgeSubtype(s)}>
                          {s}
                        </StatusBadge>
                      );
                    })()}
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="grid grid-cols-4 items-start gap-3">
                      <p className="font-medium text-right text-muted-foreground">Task ID:</p>
                      <p className="col-span-3 font-mono text-sm break-all">{task.task_id}</p>
                      
                      {task.parent_task_id && (
                        <>
                          <p className="font-medium text-right text-muted-foreground">Parent Task:</p>
                          <p className="col-span-3 font-mono text-sm break-all">{task.parent_task_id}</p>
                        </>
                      )}
                      
                      {task.event_count && (
                        <>
                          <p className="font-medium text-right text-muted-foreground">Events:</p>
                          <p className="col-span-3">{task.event_count}</p>
                        </>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-4 items-start gap-3">
                      {task.timestamp && (
                        <>
                          <p className="font-medium text-right text-muted-foreground">Timestamp:</p>
                          <p className="col-span-3">{new Date(task.timestamp).toLocaleString()}</p>
                        </>
                      )}
                      
                      {task.client_id && (
                        <>
                          <p className="font-medium text-right text-muted-foreground">Client ID:</p>
                          <p className="col-span-3 font-mono text-sm break-all">{task.client_id}</p>
                        </>
                      )}
                      
                      {task.token_id && (
                        <>
                          <p className="font-medium text-right text-muted-foreground">Token ID:</p>
                          <p className="col-span-3 font-mono text-sm break-all">{task.token_id}</p>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {/* Task details section */}
                  {task.details && Object.keys(task.details).length > 0 && (
                    <div className="mt-4">
                      <Separator className="my-4" />
                      <p className="font-medium mb-2">Details</p>
                      <div className="mt-2 border rounded-md p-3 bg-muted max-h-[300px] overflow-auto">
                        <pre className="text-xs whitespace-pre-wrap break-all">
                          {JSON.stringify(task.details, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                  
                  {/* All events section */}
                  {task.events && task.events.length > 1 && (
                    <div className="mt-4">
                      <Separator className="my-4" />
                      <p className="font-medium mb-2">All Events ({task.events.length})</p>
                      <div className="border rounded-md divide-y overflow-hidden max-h-[400px] overflow-y-auto">
                        {task.events.map((event, index) => (
                          <div key={event.log_id || index} className="p-3 hover:bg-muted">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {(() => {
                                  const s = getEventStatus(event);
                                  return (
                                    <StatusBadge subtype={getBadgeSubtype(s)}>
                                      {s}
                                    </StatusBadge>
                                  );
                                })()}
                                <span className="font-medium">{formatEventTitle(event)}</span>
                                <span className="ml-2 rounded bg-muted px-1 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                                  {(event as any).type || 'unknown'}
                                </span>
                              </div>
                              <span className="text-sm text-muted-foreground">
                                {event.timestamp ? new Date(event.timestamp).toLocaleString() : ''}
                              </span>
                            </div>
                            
                            {event.details && Object.keys(event.details).length > 0 && (
                              <div className="mt-2 pl-2 border-l-2 text-sm">
                                <div className="border rounded-md p-2 bg-muted/50">
                                  <pre className="text-xs whitespace-pre-wrap break-all">
                                    {JSON.stringify(event.details, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>No Task Details</AlertTitle>
              <AlertDescription>No task details available for this chain.</AlertDescription>
            </Alert>
          )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
