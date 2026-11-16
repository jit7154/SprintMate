import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { History, ChevronDown, ChevronUp, ShieldCheck, Filter } from "lucide-react";

export const AuditLogPage: React.FC = () => {
  const [filterEntity, setFilterEntity] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["auditLogs", filterEntity],
    queryFn: () => api.getAuditLogs(filterEntity === "ALL" ? undefined : { entity_type: filterEntity }),
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-card border border-border p-4 rounded-xl shadow-xs">
        <div className="flex items-center space-x-2">
          <History className="h-5 w-5 text-primary" />
          <div>
            <h1 className="text-base font-bold text-foreground">Append-Only Audit Log</h1>
            <p className="text-xs text-muted-foreground">
              Cryptographically timestamped audit trail of all human approvals, state re-checks, and mutations
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-xs text-muted-foreground font-medium">Entity:</label>
          <select
            value={filterEntity}
            onChange={(e) => setFilterEntity(e.target.value)}
            className="text-xs bg-secondary border border-border rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="ALL">All Entities</option>
            <option value="proposal">Proposals</option>
            <option value="issue">Issues</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-card border border-border rounded-xl shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No audit log entries recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-secondary/60 border-b border-border text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.map((log) => {
                  const isExpanded = expandedId === log.id;

                  return (
                    <React.Fragment key={log.id}>
                      <tr
                        onClick={() => setExpandedId(isExpanded ? null : log.id)}
                        className="hover:bg-secondary/40 transition-colors cursor-pointer"
                      >
                        <td className="py-3.5 px-4 font-mono text-[11px] text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-mono font-bold text-foreground">
                            {log.entity_type} #{log.entity_id}
                          </span>
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-semibold text-foreground">{log.action}</span>
                        </td>

                        <td className="py-3.5 px-4 text-foreground">{log.actor_id}</td>

                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-secondary text-secondary-foreground border border-border">
                            {log.actor_role}
                          </span>
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              log.outcome === "SUCCESS"
                                ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                                : "bg-red-500/15 text-red-500 border border-red-500/30"
                            }`}
                          >
                            {log.outcome}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <button className="text-muted-foreground hover:text-foreground">
                            {isExpanded ? <ChevronUp className="h-4 w-4 inline" /> : <ChevronDown className="h-4 w-4 inline" />}
                          </button>
                        </td>
                      </tr>

                      {/* State Diff Expansion Row */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="bg-secondary/20 p-4 border-b border-border">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                              <div className="p-3 rounded-lg bg-card border border-border">
                                <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">
                                  State Before Mutation:
                                </span>
                                <pre className="font-mono text-[11px] text-foreground overflow-x-auto p-2 bg-secondary/50 rounded">
                                  {JSON.stringify(log.before_state, null, 2)}
                                </pre>
                              </div>

                              <div className="p-3 rounded-lg bg-card border border-border">
                                <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">
                                  State After Mutation:
                                </span>
                                <pre className="font-mono text-[11px] text-foreground overflow-x-auto p-2 bg-secondary/50 rounded">
                                  {JSON.stringify(log.after_state, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
