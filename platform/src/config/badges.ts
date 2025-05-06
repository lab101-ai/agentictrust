import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
  ShieldCheck,
  FileWarning,
  Lock,
  Unlock,
  Zap,
  FileText,
  Code,
  Database,
  Globe,
  Users,
  Bot,
  Settings,
  Wrench,
  Clock,
  Calendar,
  Star,
  BookOpen,
  Tag,
  Shield,
  ShieldX,
  Power,
  PowerOff,
  LucideIcon,
  Eye, // For read
  Edit, // For write/update
  PlusCircle, // For create
  Trash2, // For delete
  KeyRound, // Generic scope
} from "lucide-react";

// Define the badge configuration interface for better type checking
export interface BadgeConfig {
  label: string;
  icon: LucideIcon;
  variant: string; // Allow any string variant for flexibility
  className: string;
}

// Define badge types with their properties
export const badgeTypes = {
  // Policy badges
  policy: {
    allow: {
      label: "Allow",
      icon: Shield,
      variant: "default",
      className: "bg-green-600 hover:bg-green-600/90 text-white"
    },
    deny: {
      label: "Deny",
      icon: ShieldX,
      variant: "destructive",
      className: ""
    },
    active: {
      label: "Active",
      icon: CheckCircle,
      variant: "default",
      className: "bg-green-600 hover:bg-green-600/90 text-white"
    },
    inactive: {
      label: "Inactive",
      icon: XCircle,
      variant: "outline",
      className: ""
    },
    priority: {
      label: "Priority",
      icon: Star,
      variant: "secondary",
      className: "bg-amber-500 hover:bg-amber-500/90 text-white"
    }
  },
  // Status badges
  status: {
    success: {
      label: "Success",
      icon: CheckCircle,
      variant: "default",
      className: "bg-green-600 hover:bg-green-600/90 text-white"
    },
    error: {
      label: "Error",
      icon: XCircle,
      variant: "destructive",
      className: ""
    },
    warning: {
      label: "Warning",
      icon: AlertCircle,
      variant: "secondary",
      className: "bg-yellow-500 hover:bg-yellow-500/90 text-white"
    },
    info: {
      label: "Info",
      icon: Info,
      variant: "secondary",
      className: "bg-blue-500 hover:bg-blue-500/90 text-white"
    },
    pending: {
      label: "Pending",
      icon: Clock,
      variant: "secondary",
      className: "bg-orange-500 hover:bg-orange-500/90 text-white"
    },
    inactive: {
      label: "Inactive",
      icon: XCircle,
      variant: "secondary",
      className: ""
    }
  },
  
  // Security badges
  security: {
    secure: {
      label: "Secure",
      icon: ShieldCheck,
      variant: "outline",
      className: "text-green-600 border-green-600"
    },
    warning: {
      label: "Warning",
      icon: FileWarning,
      variant: "outline",
      className: "text-yellow-500 border-yellow-500"
    },
    locked: {
      label: "Locked",
      icon: Lock,
      variant: "outline",
      className: "text-red-500 border-red-500"
    },
    unlocked: {
      label: "Unlocked",
      icon: Unlock,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    }
  },

  // Resource types
  resource: {
    api: {
      label: "API",
      icon: Zap,
      variant: "outline",
      className: "text-purple-500 border-purple-500"
    },
    document: {
      label: "Document",
      icon: FileText,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    },
    code: {
      label: "Code",
      icon: Code,
      variant: "outline",
      className: "text-emerald-500 border-emerald-500"
    },
    database: {
      label: "Database",
      icon: Database,
      variant: "outline",
      className: "text-amber-500 border-amber-500"
    },
    web: {
      label: "Web",
      icon: Globe,
      variant: "outline",
      className: "text-sky-500 border-sky-500"
    }
  },

  // User roles
  role: {
    admin: {
      label: "Admin",
      icon: ShieldCheck,
      variant: "outline",
      className: "text-red-500 border-red-500"
    },
    user: {
      label: "User",
      icon: Users,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    },
    agent: {
      label: "Agent",
      icon: Bot,
      variant: "outline",
      className: "text-purple-500 border-purple-500"
    },
    system: {
      label: "System",
      icon: Settings,
      variant: "outline",
      className: "text-gray-500 border-gray-500"
    }
  },
  
  // Tool types
  tool: {
    utility: {
      label: "Utility",
      icon: Wrench,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    },
    analytics: {
      label: "Analytics",
      icon: FileText,
      variant: "outline",
      className: "text-emerald-500 border-emerald-500"
    },
    integration: {
      label: "Integration",
      icon: Globe,
      variant: "outline",
      className: "text-amber-500 border-amber-500"
    }
  },
  
  // Time-related
  time: {
    recent: {
      label: "Recent",
      icon: Clock,
      variant: "outline",
      className: "text-green-500 border-green-500"
    },
    scheduled: {
      label: "Scheduled",
      icon: Calendar,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    },
    expired: {
      label: "Expired",
      icon: Clock,
      variant: "outline",
      className: "text-red-500 border-red-500"
    }
  },
  
  // Importance
  importance: {
    critical: {
      label: "Critical",
      icon: AlertCircle,
      variant: "outline",
      className: "text-red-600 border-red-600"
    },
    high: {
      label: "High",
      icon: Star,
      variant: "outline",
      className: "text-orange-500 border-orange-500"
    },
    medium: {
      label: "Medium",
      icon: BookOpen,
      variant: "outline",
      className: "text-yellow-500 border-yellow-500"
    },
    low: {
      label: "Low",
      icon: Tag,
      variant: "outline",
      className: "text-blue-500 border-blue-500"
    }
  },
  // Scope badges
  scope: {
    read: {
      label: "Read",
      icon: Eye,
      variant: "outline",
      className: "text-blue-600 border-blue-600"
    },
    write: {
      label: "Write",
      icon: Edit,
      variant: "outline",
      className: "text-orange-600 border-orange-600"
    },
    create: {
      label: "Create",
      icon: PlusCircle,
      variant: "outline",
      className: "text-green-600 border-green-600"
    },
    delete: {
      label: "Delete",
      icon: Trash2,
      variant: "outline",
      className: "text-red-600 border-red-600"
    },
    admin: {
      label: "Admin",
      icon: ShieldCheck,
      variant: "outline",
      className: "text-purple-600 border-purple-600"
    }
  }
};

// Helper function to get badge configuration
export const getBadgeConfig = (
  type: keyof typeof badgeTypes,
  subtype: string
): BadgeConfig => {
  // Default configuration if type or subtype is not found
  const defaultConfig: BadgeConfig = {
    label: subtype, // Use subtype name as label by default
    icon: KeyRound, // Generic key icon
    variant: "secondary",
    className: "text-gray-500 border-gray-500",
  };

  const typeConfig = badgeTypes[type];
  if (!typeConfig) return defaultConfig; // Type doesn't exist

  // Special handling for scope: Use default style if specific subtype isn't defined
  if (type === 'scope') {
    const scopeSubtypeConfig = typeConfig[subtype as keyof typeof typeConfig];
    if (scopeSubtypeConfig) {
      return scopeSubtypeConfig; // Return specific scope config if found
    }
    // Fallback to generic scope styling
    return {
      label: subtype, // Use the actual scope name
      icon: KeyRound, // Generic key icon
      variant: 'outline',
      className: 'text-blue-600 border-blue-600'
    };
  }

  // For other types, check if the subtype exists
  const subtypeConfig = typeConfig[subtype as keyof typeof typeConfig];

  return subtypeConfig || defaultConfig; // Return subtype config or default
};

// Get all badge types as options for UI components
export function getBadgeTypeOptions() {
  return Object.keys(badgeTypes).map(type => ({
    value: type,
    label: type.charAt(0).toUpperCase() + type.slice(1)
  }));
}

// Type definition for the return value of getBadgeSubtypeOptions
interface BadgeSubtypeOption {
  value: string;
  label: string;
}

// Get subtypes for a given type
export function getBadgeSubtypeOptions(type: keyof typeof badgeTypes): BadgeSubtypeOption[] {
  if (!badgeTypes[type]) return [];
  
  return Object.keys(badgeTypes[type]).map(subtype => {
    // Properly type the subtype to access the badge configuration
    const subtypeKey = subtype as keyof typeof badgeTypes[typeof type];
    const badgeConfig = badgeTypes[type][subtypeKey] as BadgeConfig;
    
    // Add a fallback in case label is not available
    return {
      value: subtype,
      label: badgeConfig.label || subtype // Fallback to the key if label is missing
    };
  });
}
