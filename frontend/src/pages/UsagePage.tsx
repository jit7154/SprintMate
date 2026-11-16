import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { BarChart2, Clock, Coins, Cpu, Activity } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export const UsagePage: React.FC = () => {
  const { data: usage, isLoading } = useQuery({
    queryKey: ["usageSummary"],
    queryFn: () => api.getUsageSummary(),
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const records = usage?.records || [];
  const chartData = records.slice(0, 10).reverse().map((r, i) => ({
    query: `Q${i + 1}`,
    latency: Math.round(r.latency_ms),
    tokens: r.input_tokens + r.output_tokens,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-card border border-border p-6 rounded-xl shadow-xs">
        <div className="flex items-center space-x-2">
          <BarChart2 className="h-5 w-5 text-primary" />
          <div>
            <h1 className="text-base font-bold text-foreground">AI Agent Observability & Gemini Telemetry</h1>
            <p className="text-xs text-muted-foreground">
              Production telemetry measuring token consumption, API latency percentiles, and estimated inference cost
            </p>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border p-5 rounded-xl shadow-xs flex items-center space-x-4">
          <div className="p-3 rounded-lg bg-primary/10 text-primary">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground font-medium">Investigations</span>
            <p className="text-2xl font-bold text-foreground mt-0.5">
              {usage?.total_investigations || 0}
            </p>
          </div>
        </div>

        <div className="bg-card border border-border p-5 rounded-xl shadow-xs flex items-center space-x-4">
          <div className="p-3 rounded-lg bg-blue-500/10 text-blue-500">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground font-medium">Latency (Avg / p95)</span>
            <p className="text-xl font-bold text-foreground mt-0.5">
              {Math.round(usage?.average_latency_ms || 0)}ms{" "}
              <span className="text-xs font-normal text-muted-foreground">
                ({Math.round(usage?.p95_latency_ms || 0)}ms)
              </span>
            </p>
          </div>
        </div>

        <div className="bg-card border border-border p-5 rounded-xl shadow-xs flex items-center space-x-4">
          <div className="p-3 rounded-lg bg-purple-500/10 text-purple-500">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground font-medium">Total Tokens</span>
            <p className="text-xl font-bold text-foreground mt-0.5">
              {usage?.total_tokens || 0}
            </p>
            <span className="text-[10px] text-muted-foreground">
              {usage?.total_input_tokens} in / {usage?.total_output_tokens} out
            </span>
          </div>
        </div>

        <div className="bg-card border border-border p-5 rounded-xl shadow-xs flex items-center space-x-4">
          <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-500">
            <Coins className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground font-medium">Estimated Cost</span>
            <p className="text-xl font-bold text-emerald-500 mt-0.5">
              ${(usage?.total_estimated_cost_usd || 0).toFixed(6)}
            </p>
            <span className="text-[10px] text-muted-foreground">Gemini API pricing</span>
          </div>
        </div>
      </div>

      {/* Latency Chart */}
      {chartData.length > 0 && (
        <div className="bg-card border border-border p-6 rounded-xl shadow-xs">
          <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">
            Recent Query Latencies (ms)
          </h2>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-border" />
                <XAxis dataKey="query" stroke="currentColor" className="text-muted-foreground text-xs" />
                <YAxis stroke="currentColor" className="text-muted-foreground text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    borderColor: "hsl(var(--border))",
                    borderRadius: "0.5rem",
                    fontSize: "0.75rem",
                  }}
                />
                <Bar dataKey="latency" name="Latency (ms)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Query Logs Table */}
      <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-border bg-secondary/30">
          <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">
            Detailed Request Execution Log
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-secondary/60 border-b border-border text-muted-foreground uppercase text-[10px]">
              <tr>
                <th className="py-3 px-4">Time</th>
                <th className="py-3 px-4">Query</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Tokens</th>
                <th className="py-3 px-4">Est. Cost</th>
                <th className="py-3 px-4">Tools Called</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-secondary/30 transition-colors">
                  <td className="py-3 px-4 font-mono text-[10px] text-muted-foreground">
                    {new Date(r.created_at).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4 font-medium text-foreground max-w-xs truncate">
                    {r.query}
                  </td>
                  <td className="py-3 px-4 font-mono">{Math.round(r.latency_ms)}ms</td>
                  <td className="py-3 px-4 font-mono text-muted-foreground">
                    {r.input_tokens + r.output_tokens}
                  </td>
                  <td className="py-3 px-4 font-mono text-emerald-500">
                    ${r.estimated_cost_usd.toFixed(6)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {r.tools_called.map((t, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.2 rounded bg-muted text-muted-foreground font-mono text-[9px] border border-border"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
