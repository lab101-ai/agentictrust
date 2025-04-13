// Dashboard configuration

import { 
  BarChart, 
  Users, 
  Wrench, 
  Key, 
  Shield, 
  ClipboardList 
} from "lucide-react";

// Define tab configuration
export const dashboardTabs = [
  { 
    id: "overview", 
    label: "Overview",
    icon: BarChart,
    description: "Platform status and metrics" 
  },
  { 
    id: "agents", 
    label: "Agents",
    icon: Users,
    description: "View and manage AI agents" 
  },
  { 
    id: "tools", 
    label: "Tools",
    icon: Wrench,
    description: "Configure agent tools and capabilities" 
  },
  { 
    id: "tokens", 
    label: "Tokens",
    icon: Key,
    description: "Manage access tokens and sessions" 
  },
  { 
    id: "scopes", 
    label: "Scopes",
    icon: Shield,
    description: "Control permission scopes and access levels" 
  },
  { 
    id: "audit", 
    label: "Audit",
    icon: ClipboardList,
    description: "View platform activity logs" 
  }
];

// Default tab
export const defaultTab = "overview";

// Get tab by ID
export function getTabById(id: string | null) {
  return dashboardTabs.find(tab => tab.id === id) || dashboardTabs[0];
}
