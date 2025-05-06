// Dashboard configuration

import { 
  Bot, 
  BarChart, 
  Users, 
  Wrench, 
  Key, 
  Shield, 
  ClipboardList,
  Globe,
} from "lucide-react";

// Import additional icon
import { FileCode } from "lucide-react";

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
    icon: Bot,
    description: "View and manage AI agents" 
  },
  { 
    id: "tools", 
    label: "Tools",
    icon: Wrench,
    description: "Configure agent tools and capabilities" 
  },
  { 
    id: "scopes", 
    label: "Scopes",
    icon: Shield,
    description: "Control permission scopes and access levels" 
  },
  { 
    id: "policies", 
    label: "Policies",
    icon: FileCode,
    description: "Manage attribute-based access control policies" 
  },
  { 
    id: "tokens", 
    label: "Tokens",
    icon: Key,
    description: "Manage access tokens and sessions" 
  },
  { 
    id: "users",
    label: "Users",
    icon: Users,
    description: "Manage platform users"
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
