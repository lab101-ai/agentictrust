"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Tool } from "@/lib/api";
import { ToolForm } from "@/components/dashboard/tool/tool-form";

// Default initial tool state
const defaultTool: Tool = {
  tool_id: "", // Will be assigned by the API
  name: "",
  description: "",
  category: "",
  permissions_required: [],
  is_active: true,
  inputSchema: {
    type: "object",
    properties: {},
    required: []
  }
};

export default function NewToolPage() {
  const [initialTool, setInitialTool] = useState<Tool | undefined>();

  useEffect(() => {
    // Check for template in localStorage
    const checkForTemplate = () => {
      try {
        const templateData = localStorage.getItem('toolTemplate');
        if (templateData) {
          const templateObj = JSON.parse(templateData);
          // Create a tool from template
          const toolFromTemplate = {
            ...defaultTool,
            name: templateObj.name || defaultTool.name,
            description: templateObj.description || defaultTool.description,
            category: templateObj.category || defaultTool.category,
            permissions_required: templateObj.permissions_required || defaultTool.permissions_required,
            inputSchema: templateObj.inputSchema || defaultTool.inputSchema
          };
          
          setInitialTool(toolFromTemplate);
          
          // Clear the template from localStorage to prevent reloading it on refresh
          localStorage.removeItem('toolTemplate');
          toast.info("Template applied to new tool");
        } else {
          // Set the default tool if no template is found
          setInitialTool(defaultTool);
        }
      } catch (error) {
        console.error("Error loading template:", error);
        // Clear potentially corrupted data and use default
        localStorage.removeItem('toolTemplate');
        setInitialTool(defaultTool);
      }
    };

    checkForTemplate();
  }, []);

  if (!initialTool) {
    return null; // Return null or a loading spinner until the initialTool is set
  }

  return <ToolForm isNew={true} initialTool={initialTool} />;
}
