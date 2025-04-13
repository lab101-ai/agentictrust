"use client";

import { Card, CardContent } from "@/components/ui/card";

interface StatsCardProps {
  value: string | number;
  label: string;
  trend?: number; // Percentage change, positive or negative
}

export function StatsCard({ value, label, trend }: StatsCardProps) {
  const isLoading = value === "...";
  
  return (
    <Card className="overflow-hidden transition-all duration-300 hover:shadow-md">
      <CardContent className="p-6">
        <div className="mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">{label}</h3>
        </div>
        
        <div className={`text-3xl font-bold transition-opacity duration-300 ${isLoading ? 'opacity-50' : 'opacity-100'}`}>
          {isLoading ? 
            <div className="h-8 w-16 bg-muted rounded animate-pulse"></div> : 
            value
          }
        </div>
        
        {trend !== undefined && !isLoading && (
          <div className={`flex items-center mt-2 text-sm ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            <span>{trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%</span>
            <span className="text-muted-foreground ml-1">vs last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 