"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { PolicyAPI, type PolicyRegistration } from "@/lib/api";
import { ArrowLeft, Copy, Shield, Clock, Users, Globe, FileCode, Lock, ChevronDown, ChevronUp, Maximize2, Minimize2 } from "lucide-react";
import { IconBadge, PolicyBadge } from "@/components/ui/icon-badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

// Policy templates for common use cases
const POLICY_TEMPLATES = [
  {
    id: "time-based",
    name: "Business Hours Access",
    description: "Allow access only during business hours (9AM to 5PM)",
    icon: Clock,
    category: "Time-Based",
    template: {
      name: "Business Hours Access",
      description: "Allow access only during business hours (9AM to 5PM)",
      effect: "allow" as const,
      conditions: {
        and: [
          {
            attribute: "environment.time.hour",
            operator: "gte",
            value: 9
          },
          {
            attribute: "environment.time.hour",
            operator: "lt",
            value: 17
          },
          {
            attribute: "environment.time.is_business_hours",
            operator: "eq",
            value: true
          }
        ]
      },
      priority: 20,
      is_active: true
    }
  },
  {
    id: "owner-access",
    name: "Resource Owner Access",
    description: "Allow access only if the agent is the owner of the resource",
    icon: Users,
    category: "Ownership",
    template: {
      name: "Resource Owner Access",
      description: "Allow access only if the agent is the owner of the resource",
      effect: "allow" as const,
      conditions: {
        and: [
          {
            attribute: "agent.authenticated",
            operator: "eq",
            value: true
          },
          {
            attribute: "agent.id",
            operator: "eq",
            value: "${resource.owner_id}"
          }
        ]
      },
      priority: 30,
      is_active: true
    }
  },
  {
    id: "role-based",
    name: "Admin Role Access",
    description: "Allow full access for users with admin role",
    icon: Shield,
    category: "Role-Based",
    template: {
      name: "Admin Role Access",
      description: "Allow full access for users with admin role",
      effect: "allow" as const,
      conditions: {
        and: [
          {
            attribute: "agent.authenticated",
            operator: "eq",
            value: true
          },
          {
            attribute: "agent.role",
            operator: "eq",
            value: "admin"
          }
        ]
      },
      priority: 10,
      is_active: true
    }
  },
  {
    id: "location-based",
    name: "Location Restrictions",
    description: "Deny access from specified locations or IP ranges",
    icon: Globe,
    category: "Geographic",
    template: {
      name: "Location Restrictions",
      description: "Deny access from specified locations or IP ranges",
      effect: "deny" as const,
      conditions: {
        or: [
          {
            attribute: "environment.network.ip",
            operator: "starts_with",
            value: "192.168.1"
          },
          {
            attribute: "environment.location.country",
            operator: "in",
            value: ["BLOCKED_COUNTRY_1", "BLOCKED_COUNTRY_2"]
          }
        ]
      },
      priority: 5,
      is_active: true
    }
  },
  {
    id: "action-based",
    name: "Read-Only Access",
    description: "Allow only read operations on resources",
    icon: FileCode,
    category: "Action-Based",
    template: {
      name: "Read-Only Access",
      description: "Allow only read operations on resources",
      effect: "allow" as const,
      conditions: {
        and: [
          {
            attribute: "agent.authenticated",
            operator: "eq",
            value: true
          },
          {
            attribute: "action.type",
            operator: "in",
            value: ["read", "list", "get"]
          }
        ]
      },
      priority: 15,
      is_active: true
    }
  },
  {
    id: "multi-factor",
    name: "Multi-Factor Authenticated",
    description: "Allow access only for users with MFA enabled",
    icon: Lock,
    category: "Security",
    template: {
      name: "Multi-Factor Authentication Required",
      description: "Allow access only for users with MFA enabled",
      effect: "allow" as const,
      conditions: {
        and: [
          {
            attribute: "agent.authenticated",
            operator: "eq",
            value: true
          },
          {
            attribute: "agent.mfa_verified",
            operator: "eq",
            value: true
          }
        ]
      },
      priority: 25,
      is_active: true
    }
  }
];

export default function PolicyTemplatesPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const router = useRouter();
  
  const toggleExpanded = (templateId: string) => {
    setExpandedCards(prev => ({
      ...prev,
      [templateId]: !prev[templateId]
    }));
  };

  // Navigate to create page with template data
  const navigateToCreateWithTemplate = (template: any) => {
    // Store template data in localStorage to access it on the create page
    const templateData = {
      ...template.template,
      name: template.name,
      description: template.description
    };
    localStorage.setItem('policyTemplate', JSON.stringify(templateData));
    // Navigate to create page
    router.push("/dashboard/policies/new");
  };
  
  // Copy template to clipboard
  const copyTemplateToClipboard = (template: any) => {
    try {
      navigator.clipboard.writeText(JSON.stringify(template.template, null, 2));
      toast.success(`${template.name} template copied to clipboard`);
    } catch (error) {
      toast.error('Failed to copy template to clipboard');
    }
  };

  // Group templates by category
  const templatesByCategory = POLICY_TEMPLATES.reduce((acc, template) => {
    if (!acc[template.category]) {
      acc[template.category] = [];
    }
    acc[template.category].push(template);
    return acc;
  }, {} as Record<string, typeof POLICY_TEMPLATES>);

  return (
    <div className="container py-6">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => router.back()} className="mr-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-semibold">Policy Templates</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        <div className="lg:col-span-3">
          <p className="text-muted-foreground">
            Choose from pre-built policy templates to quickly implement common access control patterns.
            These templates can be used as-is or customized to fit your specific requirements.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-start justify-start lg:justify-end">
          {Object.keys(templatesByCategory).map((category) => (
            <Button key={category} variant="outline" size="sm" className="text-xs" onClick={() => document.getElementById(category)?.scrollIntoView({ behavior: 'smooth' })}>
              {category === "Time-Based" && <Clock className="h-3 w-3 mr-1" />}
              {category === "Ownership" && <Users className="h-3 w-3 mr-1" />}
              {category === "Role-Based" && <Shield className="h-3 w-3 mr-1" />}
              {category === "Network" && <Globe className="h-3 w-3 mr-1" />}
              {category === "Resource" && <FileCode className="h-3 w-3 mr-1" />}
              {category === "Security" && <Lock className="h-3 w-3 mr-1" />}
              {category}
            </Button>
          ))}
        </div>
      </div>

      {Object.keys(templatesByCategory).map((category) => (
        <div key={category} id={category} className="mb-10">
          <h2 className="text-xl font-semibold py-2 px-4 bg-muted rounded-md mb-4 flex items-center">
            {category === "Time-Based" && <Clock className="h-5 w-5 mr-2" />}
            {category === "Ownership" && <Users className="h-5 w-5 mr-2" />}
            {category === "Role-Based" && <Shield className="h-5 w-5 mr-2" />}
            {category === "Network" && <Globe className="h-5 w-5 mr-2" />}
            {category === "Resource" && <FileCode className="h-5 w-5 mr-2" />}
            {category === "Security" && <Lock className="h-5 w-5 mr-2" />}
            {category} Policies
          </h2>
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
            {templatesByCategory[category].map((template) => (
              <Card key={template.id} className="overflow-hidden shadow-sm hover:shadow transition-shadow duration-200">
                <CardHeader className="pb-1">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-base flex items-center">
                      <PolicyBadge 
                        subtype={template.template.effect === 'allow' ? 'allow' : 'deny'}
                        className="mr-2"
                      >
                        {template.name}
                      </PolicyBadge>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <PolicyBadge subtype="priority" className="text-[10px] px-1 py-0">
                        P{template.template.priority}
                      </PolicyBadge>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs h-7 w-7 p-0"
                          onClick={() => copyTemplateToClipboard(template)}
                          title="Copy template to clipboard"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          className="text-xs h-7 px-2"
                          onClick={() => navigateToCreateWithTemplate(template)}
                        >
                          Use Template
                        </Button>
                      </div>
                    </div>
                  </div>
                  <CardDescription className="mt-1 text-xs">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="py-0 px-4 pb-2">
                  {/* Priority badge moved to header */}
                  <div className="relative">
                    <div 
                      className={`text-[10px] border rounded-md p-2 bg-muted/30 font-mono overflow-hidden transition-all duration-300 ${expandedCards[template.id] ? 'h-auto max-h-[500px]' : 'max-h-64'} overflow-y-auto`}
                    >
                      <pre className="whitespace-pre-wrap text-[10px]">
                        {JSON.stringify(template.template.conditions, null, 2)}
                      </pre>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="absolute bottom-1 right-1 h-5 w-5 p-0 rounded-full bg-background/80 backdrop-blur-sm shadow-sm"
                      onClick={() => toggleExpanded(template.id)}
                      title={expandedCards[template.id] ? "Collapse" : "Expand"}
                    >
                      {expandedCards[template.id] ? (
                        <Minimize2 className="h-3 w-3" />
                      ) : (
                        <Maximize2 className="h-3 w-3" />
                      )}
                    </Button>
                    <div 
                      className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-background/80 to-transparent pointer-events-none"
                      style={{ display: expandedCards[template.id] ? 'none' : 'block' }}
                    />
                  </div>
                </CardContent>
                {/* No footer needed since we have the copy button in the header */}
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
