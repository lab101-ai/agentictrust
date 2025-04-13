"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tool } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface ViewToolDialogProps {
  tool: Tool;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ViewToolDialog({ tool, open, onOpenChange }: ViewToolDialogProps) {
  // Format JSON for display
  const formatJSON = (obj: any) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      return "Invalid JSON";
    }
  };

  // Get required properties from schema
  const getRequiredProperties = (): string[] => {
    if (!tool.inputSchema) return [];
    if (typeof tool.inputSchema !== 'object') return [];
    if (Array.isArray(tool.inputSchema)) return [];
    
    const schema = tool.inputSchema as any;
    if (!schema.required) return [];
    if (!Array.isArray(schema.required)) return [];
    
    return schema.required;
  };

  // Get properties from schema
  const getProperties = (): Record<string, any> => {
    if (!tool.inputSchema) return {};
    if (typeof tool.inputSchema !== 'object') return {};
    if (Array.isArray(tool.inputSchema)) return {};
    
    const schema = tool.inputSchema as any;
    if (!schema.properties) return {};
    
    return schema.properties;
  };

  // Check if inputSchema exists and has the expected structure
  const hasJsonSchema = (): boolean => {
    if (!tool.inputSchema) return false;
    if (typeof tool.inputSchema !== 'object') return false;
    if (Array.isArray(tool.inputSchema)) return false;
    
    const schema = tool.inputSchema as any;
    return 'properties' in schema;
  };

  const requiredProps = getRequiredProperties();
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Tool Details</DialogTitle>
          <DialogDescription>
            Viewing details for tool: {tool.name}
          </DialogDescription>
        </DialogHeader>
        
        <div className="mt-4 space-y-6">
          <div className="grid grid-cols-2 gap-8">
            {/* Left Column */}
            <div className="space-y-6">
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Basic Information</h3>
                <div className="grid grid-cols-4 items-start gap-3">
                  <p className="font-medium text-right text-muted-foreground">ID:</p>
                  <p className="col-span-3 font-mono text-sm break-all">{tool.tool_id}</p>
                  
                  <p className="font-medium text-right text-muted-foreground">Name:</p>
                  <p className="col-span-3 font-medium">{tool.name}</p>
                  
                  <p className="font-medium text-right text-muted-foreground">Description:</p>
                  <p className="col-span-3">{tool.description || "No description provided"}</p>
                  
                  <p className="font-medium text-right text-muted-foreground">Category:</p>
                  <p className="col-span-3">{tool.category || "Not categorized"}</p>
                  
                  <p className="font-medium text-right text-muted-foreground">Status:</p>
                  <div className="col-span-3">
                    <Badge variant={tool.is_active ? "default" : "secondary"}>
                      {tool.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  
                  {tool.created_at && (
                    <>
                      <p className="font-medium text-right text-muted-foreground">Created:</p>
                      <p className="col-span-3">{new Date(tool.created_at).toLocaleString()}</p>
                    </>
                  )}
                  
                  {tool.updated_at && (
                    <>
                      <p className="font-medium text-right text-muted-foreground">Last Updated:</p>
                      <p className="col-span-3">{new Date(tool.updated_at).toLocaleString()}</p>
                    </>
                  )}
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Security & Permissions</h3>
                <div className="grid grid-cols-4 items-start gap-3">
                  <p className="font-medium text-right text-muted-foreground">Required Permissions:</p>
                  <div className="col-span-3">
                    {tool.permissions_required && tool.permissions_required.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {tool.permissions_required.map((permission, index) => (
                          <Badge key={index} variant="outline">{permission}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No permissions required</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Right Column */}
            <div className="space-y-6">
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">Input Parameters</h3>
                {hasJsonSchema() ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-4 items-start gap-3">
                      <p className="font-medium text-right text-muted-foreground">Schema Type:</p>
                      <p className="col-span-3">
                        <Badge variant="outline">
                          {typeof tool.inputSchema === 'object' && !Array.isArray(tool.inputSchema) && 
                          'type' in tool.inputSchema ? tool.inputSchema.type : 'object'}
                        </Badge>
                      </p>
                    </div>

                    <div className="space-y-3">
                      <h4 className="text-md font-medium">Properties</h4>
                      {Object.entries(getProperties()).length > 0 ? (
                        <div className="space-y-4">
                          {Object.entries(getProperties()).map(([propName, propDetails]: [string, any]) => (
                            <div key={propName} className="border rounded-md p-3">
                              <div className="grid grid-cols-4 gap-2">
                                <p className="font-medium text-right text-muted-foreground">Name:</p>
                                <p className="col-span-3 font-medium">
                                  {propName} 
                                  {requiredProps.includes(propName) && <span className="text-red-500 ml-1">*</span>}
                                </p>
                                
                                {propDetails.description && (
                                  <>
                                    <p className="font-medium text-right text-muted-foreground">Description:</p>
                                    <p className="col-span-3">{propDetails.description}</p>
                                  </>
                                )}
                                
                                {propDetails.type && (
                                  <>
                                    <p className="font-medium text-right text-muted-foreground">Type:</p>
                                    <p className="col-span-3">
                                      <Badge variant="secondary">{propDetails.type}</Badge>
                                    </p>
                                  </>
                                )}
                                
                                {propDetails.format && (
                                  <>
                                    <p className="font-medium text-right text-muted-foreground">Format:</p>
                                    <p className="col-span-3">{propDetails.format}</p>
                                  </>
                                )}
                                
                                {propDetails.enum && Array.isArray(propDetails.enum) && propDetails.enum.length > 0 && (
                                  <>
                                    <p className="font-medium text-right text-muted-foreground">Allowed Values:</p>
                                    <div className="col-span-3 flex flex-wrap gap-1">
                                      {propDetails.enum.map((value: string, idx: number) => (
                                        <Badge key={idx} variant="outline" className="text-xs">{value}</Badge>
                                      ))}
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-muted-foreground">No properties defined</p>
                      )}
                    </div>
                  </div>
                ) : tool.parameters && tool.parameters.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-muted-foreground mb-2">Using legacy parameters format:</p>
                    {tool.parameters.map((param: any, index: number) => (
                      <div key={index} className="border rounded-md p-3">
                        <div className="grid grid-cols-4 gap-2">
                          <p className="font-medium text-right text-muted-foreground">Name:</p>
                          <p className="col-span-3 font-medium">
                            {param.name} 
                            {param.required && <span className="text-red-500 ml-1">*</span>}
                          </p>
                          
                          {param.description && (
                            <>
                              <p className="font-medium text-right text-muted-foreground">Description:</p>
                              <p className="col-span-3">{param.description}</p>
                            </>
                          )}
                          
                          {param.type && (
                            <>
                              <p className="font-medium text-right text-muted-foreground">Type:</p>
                              <p className="col-span-3">
                                <Badge variant="secondary">{param.type}</Badge>
                              </p>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No parameters defined for this tool</p>
                )}
              </div>
            </div>
          </div>
          
          {/* Full Schema Display - Full Width */}
          {hasJsonSchema() && (
            <div className="mt-4">
              <p className="font-medium mb-2">Complete Schema:</p>
              <pre className="bg-muted p-4 rounded-md overflow-auto text-xs font-mono">
                {formatJSON(tool.inputSchema)}
              </pre>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
} 