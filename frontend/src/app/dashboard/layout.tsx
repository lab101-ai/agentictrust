import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AgenticTrust Admin Dashboard",
  description: "Admin dashboard for AgenticTrust platform",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 bg-primary text-white py-4">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center">
            <a href="/" className="text-xl font-bold">AgenticTrust</a>
            <nav>
              <ul className="flex space-x-6">
                <li><a href="/dashboard" className="hover:underline">Dashboard</a></li>
                <li><a href="/dashboard#agents" className="hover:underline">Agents</a></li>
                <li><a href="/dashboard#tools" className="hover:underline">Tools</a></li>
                <li><a href="/dashboard#tokens" className="hover:underline">Tokens</a></li>
                <li><a href="/dashboard#audit" className="hover:underline">Audit Logs</a></li>
              </ul>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
} 