"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Scope } from "@/lib/api";
import { ScopeForm } from "@/components/dashboard/scope";

// Default initial scope state
const defaultScope: Scope = {
  scope_id: "", // Will be assigned by the API
  name: "",
  description: "",
  category: "read",
  is_sensitive: false,
  requires_approval: false,
  is_default: false,
  is_active: true
};

export default function NewScopePage() {
  const [initialScope, setInitialScope] = useState<Scope | undefined>();

  useEffect(() => {
    // Check for template in localStorage
    const checkForTemplate = () => {
      try {
        const templateData = localStorage.getItem('scopeTemplate');
        if (templateData) {
          const templateObj = JSON.parse(templateData);
          // Create a scope from template
          const scopeFromTemplate = {
            ...defaultScope,
            name: templateObj.name || defaultScope.name,
            description: templateObj.description || defaultScope.description,
            category: templateObj.category || defaultScope.category,
            is_sensitive: templateObj.is_sensitive ?? defaultScope.is_sensitive,
            requires_approval: templateObj.requires_approval ?? defaultScope.requires_approval,
            is_default: templateObj.is_default ?? defaultScope.is_default
          };
          
          setInitialScope(scopeFromTemplate);
          
          // Clear the template from localStorage to prevent reloading it on refresh
          localStorage.removeItem('scopeTemplate');
          toast.info("Template applied to new scope");
        } else {
          // Set the default scope if no template is found
          setInitialScope(defaultScope);
        }
      } catch (error) {
        console.error("Error loading template:", error);
        // Clear potentially corrupted data and use default
        localStorage.removeItem('scopeTemplate');
        setInitialScope(defaultScope);
      }
    };

    checkForTemplate();
  }, []);

  if (!initialScope) {
    return null; // Return null or a loading spinner until the initialScope is set
  }

  return <ScopeForm isNew={true} initialScope={initialScope} />;
}
