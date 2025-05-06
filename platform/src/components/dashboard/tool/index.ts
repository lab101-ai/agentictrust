// Re-export the tool components
// Use these exports in pages that need multiple components

import { type ComponentProps, type ComponentType } from 'react';

// Define types for components with their props
// This avoids direct module imports that might cause resolution issues
type ToolFormType = ComponentType<{
  id?: string;
  initialTool?: any;
  isNew?: boolean;
}>;

type ToolDetailsCardType = ComponentType<{
  tool: any;
  scopes?: any[];
  parameters?: any[];
  isLoading?: boolean;
  onChange?: (key: string, value: any) => void;
  onParameterChange?: (parameters: any[]) => void;
}>;

type ToolParametersCardType = ComponentType<{
  parameters: any[];
  onChange: (parameters: any[]) => void;
  isLoading?: boolean;
}>;

// Use dynamic imports to avoid TypeScript module resolution issues
const ToolFormDynamic = require('./tool-form').ToolForm as ToolFormType;
const ToolDetailsCardDynamic = require('./tool-details-card').ToolDetailsCard as ToolDetailsCardType;
const ToolParametersCardDynamic = require('./tool-parameters-card').ToolParametersCard as ToolParametersCardType;

// Export the dynamically imported components
export const ToolForm = ToolFormDynamic;
export const ToolDetailsCard = ToolDetailsCardDynamic;
export const ToolParametersCard = ToolParametersCardDynamic;
