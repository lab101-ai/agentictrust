"use client";

import { useState, useEffect } from "react";
import { Tool, ToolAPI } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { RegisterToolDialog } from "@/components/dashboard/RegisterToolDialog";
import ToolActions from "@/components/dashboard/ToolActions";

export function ToolsTab() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchTools = async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await ToolAPI.getAll();
      setTools(data);
    } catch (err) {
      setError(true);
      toast.error("Failed to load tools");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  return (
    <Card id="tools">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Available Tools</CardTitle>
          <CardDescription>View and manage agent tools</CardDescription>
        </div>
        <RegisterToolDialog onToolAdded={fetchTools} />
      </CardHeader>
      <CardContent>
        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading tools</AlertTitle>
            <AlertDescription>There was a problem fetching the tools data.</AlertDescription>
          </Alert>
        ) : loading ? (
          <div className="space-y-4">
            {Array(4).fill(0).map((_, i) => (
              <Skeleton key={`tool-skeleton-${i}`} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            {tools.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tools.map((tool) => (
                    <TableRow key={tool.tool_id}>
                      <TableCell className="font-medium">{tool.name}</TableCell>
                      <TableCell className="max-w-[300px] truncate">{tool.description || "No description"}</TableCell>
                      <TableCell>
                        {tool.category ? (
                          <Badge variant="outline">{tool.category}</Badge>
                        ) : (
                          <span className="text-muted-foreground">Uncategorized</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={tool.is_active ? "default" : "secondary"}>
                          {tool.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ToolActions tool={tool} onUpdate={fetchTools} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="bg-muted p-4 rounded-md text-center">
                No tools registered yet. Click "Register New Tool" to create one.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
