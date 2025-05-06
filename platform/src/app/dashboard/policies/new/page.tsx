"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Policy } from "@/lib/api";
import { PolicyForm } from "@/components/dashboard/policy";

// Default initial policy state with appropriate conditions
const defaultPolicy: Policy = {
  policy_id: "", // Will be assigned by the API
  name: "",
  description: "",
  effect: "allow",
  conditions: {
    attribute: "agent.authenticated",
    operator: "eq",
    value: true
  },
  priority: 10,
  is_active: true,
  scope_id: "none"
};

export default function NewPolicyPage() {
  const [initialPolicy, setInitialPolicy] = useState<Policy | undefined>();

  useEffect(() => {
    // Check for template in localStorage
    const checkForTemplate = () => {
      try {
        const templateData = localStorage.getItem('policyTemplate');
        if (templateData) {
          const templateObj = JSON.parse(templateData);
          // Create a policy from template
          const policyFromTemplate = {
            ...defaultPolicy,
            name: templateObj.name || defaultPolicy.name,
            description: templateObj.description || defaultPolicy.description,
            conditions: templateObj.conditions || defaultPolicy.conditions,
            effect: templateObj.effect || defaultPolicy.effect,
            priority: templateObj.priority || defaultPolicy.priority
          };
          
          setInitialPolicy(policyFromTemplate);
          
          // Clear the template from localStorage to prevent reloading it on refresh
          localStorage.removeItem('policyTemplate');
          toast.info("Template applied to new policy");
        } else {
          // Set the default policy if no template is found
          setInitialPolicy(defaultPolicy);
        }
      } catch (error) {
        console.error("Error loading template:", error);
        // Clear potentially corrupted data and use default
        localStorage.removeItem('policyTemplate');
        setInitialPolicy(defaultPolicy);
      }
    };

    checkForTemplate();
  }, []);

  if (!initialPolicy) {
    return null; // Return null or a loading spinner until the initialPolicy is set
  }

  return <PolicyForm isNew={true} initialPolicy={initialPolicy} />;
}
