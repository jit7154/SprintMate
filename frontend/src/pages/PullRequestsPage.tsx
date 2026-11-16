import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import {
  GitPullRequest,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  Search,
  ExternalLink,
} from "lucide-react";

export const PullRequestsPage: React.FC = () => {
  const [stuckOnly, setStuckOnly] = useState(false);
  const [search, setSearch] = useState("");

  const { data: pullRequests = [], isLoading } = useQuery({
    queryKey: ["pullRequests", stuckOnly],
    queryFn: () => api.getPullRequests({ stuck_only: stuckOnly }),
  });

  const filtered = pullRequests.filter((pr) => {
    return (
      pr.title.toLowerCase().includes(search.toLowerCase()) ||
      pr.branch.toLowerCase().includes(search.toLowerCase()) ||
      String(pr.pr_number).includes(search) ||
      (pr.issue_key || "").toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="space-y-4">
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-card border border-border p-4 rounded-xl shadow-xs">
        <div className="flex items-center space-x-2">
          <GitPullRequest className="h-5 w-5 text-primary" />
          <div>
            <h1 className="text-base font-bold text-foreground">Pull Requests & CI Signals</h1>
            <p className="text-xs text-muted-foreground">
              Detecting code review stagnation and failing automated integration suites
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter PR #, title, or key..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-secondary text-xs rounded-lg border border-border focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <button
            onClick={() => setStuckOnly(!stuckOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              stuckOnly
                ? "bg-red-500/10 text-red-500 border-red-500/30"
                : "bg-secondary text-foreground border-border hover:bg-secondary/80"
            }`}
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Stuck Only</span>
          </button>
        </div>
      </div>

      {/* PR Table */}
      <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-secondary/60 border-b border-border text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4">PR #</th>
                  <th className="py-3 px-4">Title & Branch</th>
                  <th className="py-3 px-4">Author</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4">Age</th>
                  <th className="py-3 px-4">CI Status</th>
                  <th className="py-3 px-4">Linked Issue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((pr) => (
                  <tr
                    key={pr.id}
                    className={`hover:bg-secondary/30 transition-colors ${
                      pr.is_stuck ? "bg-red-500/5" : ""
                    }`}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-foreground">
                      #{pr.pr_number}
                    </td>

                    <td className="py-3.5 px-4 max-w-sm">
                      <div className="font-semibold text-foreground flex items-center space-x-1.5">
                        <span>{pr.title}</span>
                        {pr.is_stuck && (
                          <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-red-500/15 text-red-500 border border-red-500/30">
                            STUCK
                          </span>
                        )}
                      </div>
                      <div className="font-mono text-[10px] text-muted-foreground mt-0.5">
                        {pr.branch}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-muted-foreground">{pr.author_name}</td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium ${
                          pr.review_status === "APPROVED"
                            ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                            : pr.review_status === "CHANGES_REQUESTED"
                            ? "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                            : "bg-blue-500/15 text-blue-500 border border-blue-500/30"
                        }`}
                      >
                        {pr.review_status.replace("_", " ")}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-1 text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span className={pr.age_days && pr.age_days >= 3 ? "text-amber-500 font-semibold" : ""}>
                          {pr.age_days}d
                        </span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      {pr.latest_ci_status === "SUCCESS" && (
                        <span className="inline-flex items-center space-x-1 text-emerald-500 font-semibold text-[10px]">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>PASSING</span>
                        </span>
                      )}
                      {pr.latest_ci_status === "FAILURE" && (
                        <div className="space-y-0.5">
                          <span className="inline-flex items-center space-x-1 text-red-500 font-semibold text-[10px]">
                            <XCircle className="h-3.5 w-3.5" />
                            <span>FAILED</span>
                          </span>
                          {pr.latest_ci_step && (
                            <p className="font-mono text-[9px] text-red-400 truncate max-w-[140px]">
                              {pr.latest_ci_step}
                            </p>
                          )}
                        </div>
                      )}
                      {!pr.latest_ci_status && (
                        <span className="text-muted-foreground text-[10px]">No runs</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 font-mono font-medium text-primary">
                      {pr.issue_key ? (
                        <span className="px-1.5 py-0.5 rounded bg-primary/10 border border-primary/20">
                          {pr.issue_key}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}

                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground">
                      No pull requests match the selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
