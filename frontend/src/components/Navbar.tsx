import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useApp } from "../hooks/useAppContext";
import {
  Activity,
  Kanban,
  GitPullRequest,
  Users,
  BotMessageSquare,
  CheckSquare,
  History,
  BarChart2,
  Sun,
  Moon,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

export const Navbar: React.FC = () => {
  const { role, setRole, selectedSprintId, setSelectedSprintId, darkMode, setDarkMode } = useApp();
  const location = useLocation();

  const { data: sprints } = useQuery({
    queryKey: ["sprints"],
    queryFn: () => api.getSprints(),
  });

  const navLinks = [
    { to: "/", label: "Overview", icon: Activity },
    { to: "/board", label: "Sprint Board", icon: Kanban },
    { to: "/pull-requests", label: "Pull Requests", icon: GitPullRequest },
    { to: "/team", label: "Team Workload", icon: Users },
    { to: "/assistant", label: "AI Copilot", icon: BotMessageSquare },
    { to: "/approvals", label: "Approvals", icon: CheckSquare },
    { to: "/audit", label: "Audit Log", icon: History },
    { to: "/usage", label: "Usage & Cost", icon: BarChart2 },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand & Sprint Selector */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-lg shadow-sm">
              S
            </div>
            <div>
              <span className="font-bold tracking-tight text-foreground text-lg">SprintMate</span>
              <span className="ml-2 text-xs font-medium px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">
                DevCore
              </span>
            </div>
          </div>

          {/* Sprint Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs font-medium text-muted-foreground">Sprint:</label>
            <select
              value={selectedSprintId}
              onChange={(e) => setSelectedSprintId(Number(e.target.value))}
              aria-label="Select sprint"
              className="text-xs font-semibold bg-secondary text-foreground border border-border rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
            >
              {sprints?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.status})
                </option>
              )) || <option value={2}>Sprint 24 (ACTIVE)</option>}
            </select>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Tools: Role Switcher & Theme */}
        <div className="flex items-center space-x-3">
          {/* Role Switcher */}
          <div className="flex items-center bg-secondary p-0.5 rounded-lg border border-border text-xs">
            <button
              onClick={() => setRole("manager")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                role === "manager"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <ShieldCheck className="h-3 w-3" />
              <span>Manager</span>
            </button>
            <button
              onClick={() => setRole("developer")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                role === "developer"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <ShieldAlert className="h-3 w-3" />
              <span>Developer</span>
            </button>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            title="Toggle color theme"
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
