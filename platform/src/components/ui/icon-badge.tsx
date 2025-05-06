import React from "react";
import { Badge } from "@/components/ui/badge";
import { badgeTypes, getBadgeConfig } from "@/config/badges";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

export interface IconBadgeProps extends React.ComponentProps<typeof Badge> {
  /**
   * Badge type (from predefined categories in badgeTypes)
   */
  type?: keyof typeof badgeTypes;
  
  /**
   * Badge subtype (specific variant within a type)
   */
  subtype?: string;
  
  /**
   * Optional custom icon to override the default for the type/subtype
   */
  icon?: LucideIcon;
  
  /**
   * Badge label/content
   */
  children?: React.ReactNode;
  
  /**
   * Whether to show the icon
   * @default true
   */
  showIcon?: boolean;
  
  /**
   * Custom color class to override the default
   */
  colorClassName?: string;

  /**
   * Show required indicator (*) in the right corner
   */
  required?: boolean;
}

/**
 * Enhanced badge component with icon support and predefined types
 */
export function IconBadge({
  type = "status",
  subtype = "info",
  icon: customIcon,
  children,
  className,
  showIcon = true,
  colorClassName,
  required = false,
  ...props
}: IconBadgeProps) {
  // Get configuration based on type and subtype
  const config = getBadgeConfig(type, subtype);
  
  // Determine which icon to use (custom or from config)
  const Icon = customIcon || config.icon;
  
  return (
    <Badge
      variant={config.variant as any}
      className={cn(
        config.className,
        colorClassName, // Allow custom color class to override default
        className
      )}
      {...props}
    >
      {showIcon && Icon && <Icon className="h-3 w-3 mr-1" />}
      <span>{children || config.label}</span>
      {required && <span className="ml-1 text-red-500 font-bold">*</span>}
    </Badge>
  );
}

/**
 * Type-specific badge component creator
 */
function createTypedBadge<T extends keyof typeof badgeTypes>(type: T) {
  // Define the return type explicitly to avoid inference issues
  return function TypedBadge({
    subtype = Object.keys(badgeTypes[type])[0] as string, // Default to first subtype if not specified
    ...props
  }: Omit<IconBadgeProps, "type">) {
    // Make sure we're passing a valid string to the subtype prop
    return <IconBadge type={type} subtype={subtype} {...props} />;
  };
}

// Create pre-configured badge components for each type
export const StatusBadge = createTypedBadge("status");
export const SecurityBadge = createTypedBadge("security");
export const ResourceBadge = createTypedBadge("resource");
export const RoleBadge = createTypedBadge("role");
export const ToolBadge = createTypedBadge("tool");
export const TimeBadge = createTypedBadge("time");
export const ImportanceBadge = createTypedBadge("importance");
export const PolicyBadge = createTypedBadge("policy");
export const ScopeBadge = createTypedBadge("scope");
