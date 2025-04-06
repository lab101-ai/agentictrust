"use client";

import { Card, CardContent } from "@/components/ui/card";

interface StatsCardProps {
  value: string | number;
  label: string;
}

export function StatsCard({ value, label }: StatsCardProps) {
  return (
    <Card className="text-center">
      <CardContent className="p-6">
        <div className="text-4xl font-bold text-primary mb-2">{value}</div>
        <div className="text-sm text-muted-foreground font-medium">{label}</div>
      </CardContent>
    </Card>
  );
} 