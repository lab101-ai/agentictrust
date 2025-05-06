// Token components
// Using a similar approach to the tool components to avoid module resolution issues

import { type ComponentProps, type ComponentType } from 'react';
import { Token } from '@/lib/api';

// Define types for components with their props
type TokenDetailsCardType = ComponentType<{
  token: Token;
  isLoading?: boolean;
}>;

type TokenPermissionsCardType = ComponentType<{
  token: any; // Using any to accommodate extended token properties
  isLoading?: boolean;
}>;

type TokenViewType = ComponentType<{
  id?: string;
  initialToken?: Token;
}>;

// Use dynamic imports to avoid TypeScript module resolution issues
const TokenDetailsCardDynamic = require('./token-details-card').TokenDetailsCard as TokenDetailsCardType;
const TokenPermissionsCardDynamic = require('./token-permissions-card').TokenPermissionsCard as TokenPermissionsCardType;
const TokenViewDynamic = require('./token-view').TokenView as TokenViewType;

// Export the dynamically imported components
export const TokenDetailsCard = TokenDetailsCardDynamic;
export const TokenPermissionsCard = TokenPermissionsCardDynamic;
export const TokenView = TokenViewDynamic;
