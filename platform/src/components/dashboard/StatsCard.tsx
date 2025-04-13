"use client";

import { Card, CardContent } from "@/components/ui/card";

import { ReactNode } from "react";

interface StatsCardProps {
  title: string;
  value?: number;
  description: string;
  icon?: ReactNode;
  trend?: string; // Human readable trend text
}

export function StatsCard({ title, value, description, icon, trend }: StatsCardProps) {
  const isLoading = value === undefined;
  
  return (
    <Card className="overflow-hidden transition-all duration-300 hover:shadow-md">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-2">
          {icon && <div>{icon}</div>}
          <h3 className="text-sm font-medium">{title}</h3>
        </div>
        
        <div className={`text-3xl font-bold transition-opacity duration-300 ${isLoading ? 'opacity-50' : 'opacity-100'}`}>
          {isLoading ? 
            <div className="h-8 w-16 bg-muted rounded animate-pulse"></div> : 
            value
          }
        </div>
        
        <div className="text-sm text-muted-foreground mt-1">{description}</div>
        
        {trend && !isLoading && (
          <div className="flex items-center mt-2 text-xs text-green-600 font-medium">
            <span>{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 