"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Save } from "lucide-react";
import { ToolAPI, ScopeAPI, type Tool, type ToolRegistration, type Scope } from "@/lib/api";
import { ToolDetailsCard } from "./tool-details-card";
import { ToolParametersCard } from "./tool-parameters-card";

// Parameter type definition
interface ToolParameter {
  name: string;
  description?: string;
  required: boolean;
  type?: string;
  format?: string;
  enum?: string[];
}

interface ToolFormProps {
  id?: string;
  initialTool?: Tool;
  isNew?: boolean;
}

const DEFAULT_TOOL: ToolRegistration = {
  name: "",
  description: "",
  category: "",
  permissions_required: [],
  parameters: []
};

export const ToolForm = ({ id, initialTool, isNew = false }: ToolFormProps) => {
  const [tool, setTool] = useState<Tool | ToolRegistration>(initialTool || DEFAULT_TOOL);
  const [parameters, setParameters] = useState<ToolParameter[]>([]);
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(!initialTool);
  const router = useRouter();

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Always load scopes
        const scopesData = await ScopeAPI.getAll();
        setScopes(scopesData.filter(scope => scope.is_active !== false));

        // If editing and no initial tool provided, load the tool
        if (!isNew && !initialTool && id) {
          const toolData = await ToolAPI.get(id);
          setTool(toolData);
          
          // Extract parameters from inputSchema if available
          if (toolData.inputSchema && 
              typeof toolData.inputSchema === 'object' && 
              !Array.isArray(toolData.inputSchema) &&
              'properties' in toolData.inputSchema) {
            
            // Extract properties from JSON Schema
            const properties = (toolData.inputSchema as any).properties || {};
            
            // Extract required fields
            const required = Array.isArray((toolData.inputSchema as any).required) ? 
              (toolData.inputSchema as any).required : [];
            
            // Convert JSON Schema to parameters array
            const params: ToolParameter[] = [];
            Object.entries(properties).forEach(([name, config]: [string, any]) => {
              params.push({
                name,
                description: config.description || "",
                required: required.includes(name),
                type: config.type || "string",
                format: config.format || "",
                enum: config.enum || []
              });
            });
            
            setParameters(params);
          }
        } else if (initialTool?.inputSchema) {
          // Handle the initial tool's input schema if provided
          try {
            const schema = initialTool.inputSchema;
            if (typeof schema === 'object' && !Array.isArray(schema) && 'properties' in schema) {
              const properties = (schema as any).properties || {};
              const required = Array.isArray((schema as any).required) ? (schema as any).required : [];
              
              const params: ToolParameter[] = [];
              Object.entries(properties).forEach(([name, config]: [string, any]) => {
                params.push({
                  name,
                  description: config.description || "",
                  required: required.includes(name),
                  type: config.type || "string",
                  format: config.format || "",
                  enum: config.enum || []
                });
              });
              
              setParameters(params);
            }
          } catch (error) {
            console.error("Failed to parse input schema:", error);
          }
        }
      } catch (error) {
        toast.error(`Failed to load data: ${(error as Error).message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [id, initialTool, isNew]);

  const handleToolChange = (key: string, value: any) => {
    setTool(prev => ({ ...prev, [key]: value }));
  };

  const handleParametersChange = (newParameters: ToolParameter[]) => {
    setParameters(newParameters);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsSaving(true);
      
      // Build a JSON Schema from the parameters
      const properties: Record<string, Record<string, unknown>> = {};
      const required: string[] = [];
      
      // Convert parameters to properties
      parameters.forEach(param => {
        if (param.name) {
          properties[param.name] = {
            type: param.type || 'string'
          };
          
          if (param.description) {
            properties[param.name].description = param.description;
          }
          
          if (param.format) {
            properties[param.name].format = param.format;
          }
          
          if (param.enum && param.enum.length > 0) {
            properties[param.name].enum = param.enum;
          }
          
          if (param.required) {
            required.push(param.name);
          }
        }
      });
      
      // Create JSON Schema
      const schema: {
        type: string;
        properties: Record<string, Record<string, unknown>>;
        required?: string[];
      } = {
        type: 'object',
        properties: properties,
        required: required.length > 0 ? required : undefined
      };
      
      // Prepare the data
      const toolData: any = {
        name: tool.name,
        description: tool.description,
        category: tool.category,
        permissions_required: tool.permissions_required || [],
        inputSchema: schema,
        is_active: (tool as any).is_active !== false
      };
      
      if (isNew) {
        await ToolAPI.create(toolData);
        toast.success("Tool created successfully!");
      } else if (id) {
        await ToolAPI.update(id, toolData);
        toast.success("Tool updated successfully!");
      }
      
      router.push("/dashboard?tab=tools");
    } catch (error) {
      toast.error(`Failed to save tool: ${(error as Error).message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="container py-6">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => router.push('/dashboard?tab=tools')} className="mr-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-semibold">{isNew ? "Register Tool" : "Edit Tool"}</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
          <ToolDetailsCard 
            tool={tool}
            scopes={scopes}
            isLoading={isLoading}
            onChange={handleToolChange}
          />
          
          <ToolParametersCard 
            parameters={parameters}
            onChange={handleParametersChange}
            isLoading={isLoading}
          />
        </div>
        <div className="mt-6 flex justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/dashboard?tab=tools')}
            className="mr-2"
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                {isNew ? 'Registering' : 'Saving'}
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isNew ? 'Register Tool' : 'Save Tool'}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
