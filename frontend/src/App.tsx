import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppProvider } from "./hooks/useAppContext";
import { Navbar } from "./components/Navbar";
import { IssueDrawer } from "./components/IssueDrawer";

import { OverviewPage } from "./pages/OverviewPage";
import { BoardPage } from "./pages/BoardPage";
import { PullRequestsPage } from "./pages/PullRequestsPage";
import { TeamPage } from "./pages/TeamPage";
import { AssistantPage } from "./pages/AssistantPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { AuditLogPage } from "./pages/AuditLogPage";
import { UsagePage } from "./pages/UsagePage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 10_000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
            <Navbar />
            <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
              <Routes>
                <Route path="/" element={<OverviewPage />} />
                <Route path="/board" element={<BoardPage />} />
                <Route path="/pull-requests" element={<PullRequestsPage />} />
                <Route path="/team" element={<TeamPage />} />
                <Route path="/assistant" element={<AssistantPage />} />
                <Route path="/approvals" element={<ApprovalsPage />} />
                <Route path="/audit" element={<AuditLogPage />} />
                <Route path="/usage" element={<UsagePage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <IssueDrawer />
          </div>
        </BrowserRouter>
      </AppProvider>
    </QueryClientProvider>
  );
};

export default App;
