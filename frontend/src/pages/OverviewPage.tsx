import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useApp } from "../hooks/useAppContext";
import { formatScoreColor, formatSeverityBadge } from "../lib/utils";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingDown,
  Layers,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Link } from "react-router-dom";

export const OverviewPage: React.FC = () => {
  const { selectedSprintId, setSelectedIssue } = useApp();

  const { data: summary, isLoading, error } = useQuery({
    queryKey: ["activeSprint", selectedSprintId],
    queryFn: () => api.getActiveSprint(),
  });

  const { data: burndown } = useQuery({
    queryKey: ["burndown", selectedSprintId],
    queryFn: () => api.getBurndown(selectedSprintId),
  });

  if (isLoading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-500 font-semibold">Failed to load sprint summary.</p>
        <p className="text-xs text-muted-foreground mt-1">Make sure the backend is running on port 8001.</p>
      </div>
    );
  }

  const { sprint, risk_evaluation: risk } = summary;
  const progressPercent = Math.round((summary.completed_points / (summary.total_points || 1)) * 100);
  const daysLeft = Math.max(0, sprint.total_days - sprint.days_elapsed);

  return (
    <div className="space-y-6">
      {/* Sprint Header & Quick Stats */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                {sprint.status}
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">{sprint.name}</h1>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Goal: <span className="font-medium text-foreground">{sprint.sprint_goal}</span>
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Days Remaining</p>
              <p className="text-xl font-bold text-foreground">
                {daysLeft} <span className="text-xs font-normal text-muted-foreground">/ {sprint.total_days} days</span>
              </p>
            </div>
            <div className="text-right border-l border-border pl-4">
              <p className="text-xs text-muted-foreground">Velocity Progress</p>
              <p className="text-xl font-bold text-foreground">
                {summary.completed_points}{" "}
                <span className="text-xs font-normal text-muted-foreground">/ {summary.total_points} pts ({progressPercent}%)</span>
              </p>
            </div>
          </div>
        </div>

        {/* Sprint Timeline Progress Bar */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
            <span>Sprint Progress (Day {sprint.days_elapsed} of {sprint.total_days})</span>
            <span>{progressPercent}% Complete</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2 overflow-hidden flex">
            <div
              className="bg-primary h-2 transition-all duration-500 rounded-full"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Risk Evaluation Card + Burndown Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Evaluation Card */}
        <div className="lg:col-span-1 bg-card border border-border rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold tracking-tight text-foreground uppercase flex items-center space-x-1.5">
                <ShieldAlert className="h-4 w-4 text-primary" />
                <span>Deterministic Risk Score</span>
              </h2>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${formatScoreColor(
                  risk.overall_score
                )}`}
              >
                {risk.overall_score}/100 • {risk.risk_level}
              </span>
            </div>

            {/* Explanation */}
            <p className="text-xs text-muted-foreground leading-relaxed bg-secondary/50 p-3 rounded-lg border border-border">
              {risk.explanation}
            </p>

            {/* Category Breakdown */}
            <div className="mt-5 space-y-3">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase">Risk Breakdown</h3>
              {risk.breakdown.map((cat) => (
                <div key={cat.category} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-foreground">{cat.category_name}</span>
                    <span className="font-mono text-muted-foreground">
                      {cat.findings_count > 0 ? `${cat.findings_count} items (+${cat.points})` : "Healthy"}
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full ${
                        cat.points > 20
                          ? "bg-red-500"
                          : cat.points > 0
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, (cat.points / 35) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Automated audit verified</span>
            <Link
              to="/assistant"
              className="font-semibold text-primary hover:underline flex items-center space-x-1"
            >
              <span>Investigate root causes</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* Burndown Chart */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold tracking-tight text-foreground uppercase flex items-center space-x-1.5">
                  <TrendingDown className="h-4 w-4 text-primary" />
                  <span>Sprint Burndown (Ideal vs. Actual)</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Visualizing velocity lag and completion trajectory
                </p>
              </div>
            </div>

            <div className="h-[280px] w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={burndown || []} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-border" />
                  <XAxis dataKey="day" stroke="currentColor" className="text-muted-foreground text-xs" />
                  <YAxis stroke="currentColor" className="text-muted-foreground text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "0.5rem",
                      fontSize: "0.75rem",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
                  <Line
                    type="monotone"
                    dataKey="ideal"
                    name="Ideal Burndown"
                    stroke="#94a3b8"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual Story Points"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    connectNulls={false}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-2 pt-4 border-t border-border mt-4 text-center">
            <div className="p-2 rounded-lg bg-secondary/40">
              <span className="text-[10px] text-muted-foreground uppercase">Total</span>
              <p className="text-sm font-bold text-foreground">{summary.total_issues} issues</p>
            </div>
            <div className="p-2 rounded-lg bg-secondary/40">
              <span className="text-[10px] text-muted-foreground uppercase">Completed</span>
              <p className="text-sm font-bold text-emerald-500">{summary.completed_issues} issues</p>
            </div>
            <div className="p-2 rounded-lg bg-secondary/40">
              <span className="text-[10px] text-muted-foreground uppercase">In Progress</span>
              <p className="text-sm font-bold text-primary">{summary.in_progress_issues} issues</p>
            </div>
            <div className="p-2 rounded-lg bg-secondary/40">
              <span className="text-[10px] text-muted-foreground uppercase">Blocked</span>
              <p className="text-sm font-bold text-red-500">{summary.blocked_issues} issues</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Risks Section */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-xs">
        <h2 className="text-sm font-bold tracking-tight text-foreground uppercase mb-4 flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span>Prioritized Risk Findings ({risk.top_risks.length})</span>
        </h2>

        <div className="space-y-3">
          {risk.top_risks.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-secondary/40 border border-border flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-secondary/60 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border ${formatSeverityBadge(
                      item.severity
                    )}`}
                  >
                    {item.severity}
                  </span>
                  <span className="font-semibold text-xs text-foreground">{item.rule_name}</span>
                  <div className="flex space-x-1">
                    {item.affected_keys.map((k) => (
                      <span
                        key={k}
                        className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-primary/10 text-primary border border-primary/20 cursor-pointer"
                        onClick={() => {
                          if (k.startsWith("PR #")) return;
                          api.getSprintIssues(selectedSprintId).then((issues) => {
                            const found = issues.find((i) => i.key === k);
                            if (found) setSelectedIssue(found);
                          });
                        }}
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">{item.reason}</p>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-xs font-mono font-semibold text-red-500">+{item.weight} pts</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
