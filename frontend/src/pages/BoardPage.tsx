import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useApp } from "../hooks/useAppContext";
import { formatSeverityBadge } from "../lib/utils";
import type { Issue } from "../types";
import { AlertCircle, Clock, Link2, Search, User } from "lucide-react";

const COLUMNS: { id: Issue["status"]; label: string; color: string }[] = [
  { id: "TO_DO", label: "To Do", color: "border-slate-500/30" },
  { id: "IN_PROGRESS", label: "In Progress", color: "border-blue-500/30" },
  { id: "IN_REVIEW", label: "In Review", color: "border-amber-500/30" },
  { id: "DONE", label: "Done", color: "border-emerald-500/30" },
];

export const BoardPage: React.FC = () => {
  const { selectedSprintId, setSelectedIssue } = useApp();
  const [search, setSearch] = useState("");
  const [filterPriority, setFilterPriority] = useState<string>("ALL");

  const { data: issues = [], isLoading } = useQuery({
    queryKey: ["sprintIssues", selectedSprintId],
    queryFn: () => api.getSprintIssues(selectedSprintId),
  });

  const filteredIssues = issues.filter((issue) => {
    const matchesSearch =
      issue.key.toLowerCase().includes(search.toLowerCase()) ||
      issue.title.toLowerCase().includes(search.toLowerCase()) ||
      (issue.assignee_name || "").toLowerCase().includes(search.toLowerCase());
    const matchesPriority = filterPriority === "ALL" || issue.priority === filterPriority;
    return matchesSearch && matchesPriority;
  });

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-card border border-border p-4 rounded-xl shadow-xs">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search key, title, or assignee..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-secondary text-xs rounded-lg border border-border focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <label className="text-xs text-muted-foreground font-medium">Priority:</label>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="text-xs bg-secondary border border-border rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {COLUMNS.map((col) => {
            // Group BLOCKED issues into IN_PROGRESS or IN_REVIEW for column visualization if applicable, or show under their status
            const colIssues = filteredIssues.filter((i) => {
              if (col.id === "IN_PROGRESS") return i.status === "IN_PROGRESS" || i.status === "BLOCKED";
              return i.status === col.id;
            });

            return (
              <div key={col.id} className="bg-card/50 border border-border rounded-xl p-4 flex flex-col h-[750px]">
                {/* Column Header */}
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-border">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-xs tracking-tight text-foreground uppercase">{col.label}</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-secondary text-muted-foreground border border-border">
                      {colIssues.length}
                    </span>
                  </div>
                </div>

                {/* Cards Container */}
                <div className="space-y-3 overflow-y-auto flex-1 pr-1">
                  {colIssues.map((issue) => (
                    <div
                      key={issue.id}
                      onClick={() => setSelectedIssue(issue)}
                      className={`p-3.5 rounded-lg bg-card border transition-all cursor-pointer hover:shadow-md hover:border-primary/50 space-y-2.5 ${
                        issue.status === "BLOCKED"
                          ? "border-red-500/50 bg-red-500/5"
                          : "border-border"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-bold text-primary">
                          {issue.key}
                        </span>
                        <div className="flex items-center space-x-1">
                          {issue.status === "BLOCKED" && (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500 text-white uppercase animate-pulse">
                              BLOCKED
                            </span>
                          )}
                          <span
                            className={`text-[9px] font-semibold px-1.5 py-0.2 rounded border ${formatSeverityBadge(
                              issue.priority
                            )}`}
                          >
                            {issue.priority}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs font-semibold text-foreground line-clamp-2 leading-snug">
                        {issue.title}
                      </p>

                      {/* Card Footer: Assignee & Points & Flags */}
                      <div className="flex items-center justify-between pt-2 border-t border-border/60 text-[10px] text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <User className="h-3 w-3 text-muted-foreground" />
                          <span className="truncate max-w-[100px]">{issue.assignee_name || "Unassigned"}</span>
                        </div>

                        <div className="flex items-center space-x-2">
                          {issue.blocked_by && issue.blocked_by.length > 0 && (
                            <span className="flex items-center text-red-500 font-semibold" title={`Blocked by ${issue.blocked_by.join(", ")}`}>
                              <Link2 className="h-3 w-3 mr-0.5" />
                              {issue.blocked_by.length}
                            </span>
                          )}
                          <span className="font-bold px-1.5 py-0.5 rounded bg-secondary text-foreground">
                            {issue.story_points} pt
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}

                  {colIssues.length === 0 && (
                    <div className="h-24 flex items-center justify-center border-2 border-dashed border-border/50 rounded-lg text-xs text-muted-foreground">
                      No issues
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
