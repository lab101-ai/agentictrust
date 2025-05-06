// Agent components
// Using a similar approach to other entity components to avoid module resolution issues

import { type ComponentProps, type ComponentType } from 'react';
import { Agent } from '@/lib/api';

// Define types for components with their props
type AgentDetailsCardType = ComponentType<{
  agent: Agent;
  isLoading?: boolean;
}>;

type AgentPermissionsCardType = ComponentType<{
  agent: Agent;
  isLoading?: boolean;
}>;

type AgentViewType = ComponentType<{
  id?: string;
  initialAgent?: Agent;
}>;

type AgentFormType = ComponentType<{
  id?: string;
  initialAgent?: Agent;
  isNew?: boolean;
}>;

// Use dynamic imports to avoid TypeScript module resolution issues
const AgentDetailsCardDynamic = require('./agent-details-card').AgentDetailsCard as AgentDetailsCardType;
const AgentPermissionsCardDynamic = require('./agent-permissions-card').AgentPermissionsCard as AgentPermissionsCardType;
const AgentViewDynamic = require('./agent-view').AgentView as AgentViewType;
const AgentFormDynamic = require('./agent-form').AgentForm as AgentFormType;

// Export the dynamically imported components
export const AgentDetailsCard = AgentDetailsCardDynamic;
export const AgentPermissionsCard = AgentPermissionsCardDynamic;
export const AgentView = AgentViewDynamic;
export const AgentForm = AgentFormDynamic;
