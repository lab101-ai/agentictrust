"use client";

import { useState, FormEvent, ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuditAPI, type AuditSearchParams } from "@/lib/api";

// Define form values interface manually
interface FormValues {
  taskId: string;
  clientId: string;
  tokenId: string;
  eventType: string;
  status: string;
  fromDate: string;
  toDate: string;
}

export const AuditForm = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formValues, setFormValues] = useState<FormValues>({
    taskId: "",
    clientId: "",
    tokenId: "",
    eventType: "",
    status: "",
    fromDate: "",
    toDate: "",
  });
  const router = useRouter();
  
  // Handle form input changes
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormValues(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle select changes
  const handleSelectChange = (name: string, value: string) => {
    setFormValues(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Event types options
  const eventTypes = [
    "token_validation",
    "token_generation",
    "task_execution",
    "policy_evaluation",
    "tool_access",
    "permission_check",
  ];

  // Status options
  const statuses = [
    "success",
    "error",
    "pending",
    "warning",
  ];

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // Filter out empty fields
      const searchParams: AuditSearchParams = Object.entries(formValues).reduce((acc, [key, value]) => {
        if (value && value.trim() !== "") {
          return { ...acc, [key]: value };
        }
        return acc;
      }, {} as AuditSearchParams);
      
      // Search audit logs
      const results = await AuditAPI.search(searchParams);
      
      // Store results in local storage for the results page
      localStorage.setItem("auditSearchResults", JSON.stringify(results));
      localStorage.setItem("auditSearchParams", JSON.stringify(searchParams));
      
      toast.success("Search completed successfully");
      router.push("/dashboard/audit?tab=results");
    } catch (error) {
      toast.error(`Search failed: ${(error as Error).message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Search Audit Logs</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="taskId">Task ID</Label>
              <Input 
                id="taskId"  
                name="taskId" 
                placeholder="Enter task ID" 
                value={formValues.taskId}
                onChange={handleChange}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="clientId">Client ID (Agent)</Label>
              <Input 
                id="clientId" 
                name="clientId" 
                placeholder="Enter client ID" 
                value={formValues.clientId}
                onChange={handleChange}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="tokenId">Token ID</Label>
              <Input 
                id="tokenId" 
                name="tokenId" 
                placeholder="Enter token ID" 
                value={formValues.tokenId}
                onChange={handleChange}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="eventType">Event Type</Label>
              <Select 
                value={formValues.eventType} 
                onValueChange={(value) => handleSelectChange("eventType", value)}
              >
                <SelectTrigger id="eventType">
                  <SelectValue placeholder="Select event type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All event types</SelectItem>
                  {eventTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type.replace(/_/g, ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select 
                value={formValues.status} 
                onValueChange={(value) => handleSelectChange("status", value)}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All statuses</SelectItem>
                  {statuses.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="fromDate">From Date</Label>
              <Input 
                id="fromDate" 
                name="fromDate" 
                type="datetime-local" 
                value={formValues.fromDate}
                onChange={handleChange}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="toDate">To Date</Label>
              <Input 
                id="toDate" 
                name="toDate" 
                type="datetime-local" 
                value={formValues.toDate}
                onChange={handleChange}
              />
            </div>
          </div>
          
          <Button 
            type="submit" 
            className="w-full" 
            disabled={isSubmitting}
          >
            {isSubmitting ? "Searching..." : "Search Audit Logs"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
