"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSearchParams, useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { dashboardTabs, defaultTab } from "@/config/dashboard";
import {
  OverviewTab,
  AgentsTab,
  ToolsTab, 
  TokensTab,
  ScopesTab,
  AuditTab,
  PoliciesTab,
  UsersTab
} from "@/components/dashboard/tabs";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Update active tab when URL changes
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab') || defaultTab;
    setActiveTab(tabFromUrl);
  }, [searchParams]);

  // Function to handle tab changes
  const handleTabChange = (value: string) => {
    router.push(`/dashboard?tab=${value}`);
  };
  
  // Function to refresh data in all tabs
  const refreshData = useCallback(async () => {
    setIsRefreshing(true);
    // We'll use an event-based approach for refreshing
    window.dispatchEvent(new CustomEvent('dashboard:refresh'));
    setTimeout(() => {
      setIsRefreshing(false);
      toast.success("Dashboard data refreshed");
    }, 1000);
  }, []);

  useEffect(() => {
    // Initial data fetch handled by individual tab components
  }, []);

  return (
    <main className="flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <Button 
          variant="outline" 
          size="sm"
          className="gap-1"
          onClick={refreshData}
          disabled={isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>
      
      <div className="mt-4">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid grid-cols-8 w-full max-w-[960px] overflow-x-auto">
            {dashboardTabs.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id}>
                <tab.icon className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sr-only">{tab.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>
          
          <div className="mt-6">
            {/* Dynamic tab content generation */}
            <TabsContent value="overview">
              <OverviewTab />
            </TabsContent>
            
            <TabsContent value="agents">
              <AgentsTab />
            </TabsContent>
            
            <TabsContent value="tools">
              <ToolsTab />
            </TabsContent>
            
            <TabsContent value="tokens">
              <TokensTab />
            </TabsContent>
            
            <TabsContent value="scopes">
              <ScopesTab />
            </TabsContent>
            
            <TabsContent value="policies">
              <PoliciesTab />
            </TabsContent>
            
            <TabsContent value="audit">
              <AuditTab />
            </TabsContent>
            
            <TabsContent value="users">
              <UsersTab />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </main>
  );
}
