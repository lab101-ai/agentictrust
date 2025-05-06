"use client";

import { Card, CardContent } from "@/components/ui/card";

import { ReactNode } from "react";

interface StatsCardProps {
  title: string;
  value?: number;
  description: string;
  icon?: ReactNode;
  // trend removed for compact layout
}

export function StatsCard({ title, value, description, icon }: StatsCardProps) {
  const isLoading = value === undefined;
  
  return (
    <Card className="overflow-hidden transition-all duration-300 hover:shadow-sm text-sm">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-2">
          {icon && <div>{icon}</div>}
          <h3 className="text-sm font-medium">{title}</h3>
        </div>
        
        <div className={`text-2xl font-bold transition-opacity duration-300 ${isLoading ? 'opacity-50' : 'opacity-100'}`}>
          {isLoading ? 
            <div className="h-8 w-16 bg-muted rounded animate-pulse"></div> : 
            value
          }
        </div>
        
        <div className="text-xs text-muted-foreground mt-1">{description}</div>
      </CardContent>
    </Card>
  );
} 