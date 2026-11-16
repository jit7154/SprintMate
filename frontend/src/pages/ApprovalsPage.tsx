import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useApp } from "../hooks/useAppContext";
import {
  CheckSquare,
  Check,
  X,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  User,
  Sparkles,
} from "lucide-react";

export const ApprovalsPage: React.FC = () => {
  const { role } = useApp();
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data: proposals = [], isLoading } = useQuery({
    queryKey: ["proposals", filterStatus],
    queryFn: () => api.getProposals(filterStatus === "ALL" ? undefined : filterStatus),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => api.approveProposal(id),
    onSuccess: (data) => {
      setActionMessage({ type: "success", text: data.message });
      queryClient.invalidateQueries({ queryKey: ["proposals"] });
      queryClient.invalidateQueries({ queryKey: ["teamDevelopers"] });
      queryClient.invalidateQueries({ queryKey: ["activeSprint"] });
    },
    onError: (err: any) => {
      setActionMessage({ type: "error", text: err.message });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) => api.rejectProposal(id, reason),
    onSuccess: (data) => {
      setActionMessage({ type: "success", text: data.message });
      queryClient.invalidateQueries({ queryKey: ["proposals"] });
    },
    onError: (err: any) => {
      setActionMessage({ type: "error", text: err.message });
    },
  });

  const isManager = role === "manager";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-card border border-border p-6 rounded-xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-2.5">
            <CheckSquare className="h-5 w-5 text-primary" />
            <div>
              <h1 className="text-base font-bold text-foreground">
                Human-in-the-Loop Reassignment Proposals
              </h1>
              <p className="text-xs text-muted-foreground">
                AI agents may propose reassignments, but state changes require explicit manager approval and state re-checks.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-xs text-muted-foreground font-medium">Status Filter:</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="text-xs bg-secondary border border-border rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">All Proposals</option>
              <option value="PENDING">Pending Approval</option>
              <option value="EXECUTED">Executed</option>
              <option value="REJECTED">Rejected</option>
              <option value="STALE">Stale (Mismatch)</option>
            </select>
          </div>
        </div>

        {/* Role Alert Banner if logged in as Developer */}
        {!isManager && (
          <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center space-x-2 text-xs font-medium">
            <ShieldAlert className="h-4 w-4 shrink-0" />
            <span>
              You are currently viewing in <strong>Developer Mode (Read-Only)</strong>. Approval actions are locked. Switch to <strong>Manager</strong> in the top-right role switcher to approve or reject proposals.
            </span>
          </div>
        )}

        {/* Action Message Feedback */}
        {actionMessage && (
          <div
            className={`mt-4 p-3 rounded-lg flex items-center justify-between text-xs font-medium ${
              actionMessage.type === "success"
                ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                : "bg-red-500/10 text-red-500 border border-red-500/20"
            }`}
          >
            <span>{actionMessage.text}</span>
            <button onClick={() => setActionMessage(null)} className="font-bold underline text-[10px]">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Proposals List */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : proposals.length === 0 ? (
        <div className="bg-card border border-border p-12 rounded-xl text-center text-muted-foreground text-xs">
          No proposals found matching status filter "{filterStatus}".
        </div>
      ) : (
        <div className="space-y-4">
          {proposals.map((proposal) => {
            const isPending = proposal.status === "PENDING";

            return (
              <div
                key={proposal.id}
                className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4 hover:border-primary/40 transition-colors"
              >
                {/* Header line */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                      {proposal.issue_key}
                    </span>
                    <span className="text-xs font-semibold text-foreground">
                      Proposal #{proposal.id}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      created by {proposal.created_by} • {new Date(proposal.created_at).toLocaleString()}
                    </span>
                  </div>

                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      proposal.status === "PENDING"
                        ? "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                        : proposal.status === "EXECUTED"
                        ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                        : proposal.status === "STALE"
                        ? "bg-purple-500/15 text-purple-500 border border-purple-500/30"
                        : "bg-red-500/15 text-red-500 border border-red-500/30"
                    }`}
                  >
                    {proposal.status}
                  </span>
                </div>

                {/* Reason */}
                <p className="text-xs text-foreground bg-secondary/40 p-3 rounded-lg border border-border leading-relaxed">
                  <strong className="text-muted-foreground uppercase text-[10px] block mb-0.5">
                    Agent Rationale:
                  </strong>
                  {proposal.reason}
                </p>

                {/* Comparison Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Current Assignee */}
                  <div className="p-3.5 rounded-lg bg-secondary/30 border border-border space-y-1.5">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase">
                      Current Assignee
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="h-6 w-6 rounded-full bg-red-500/20 text-red-500 flex items-center justify-center font-bold text-xs">
                        <User className="h-3 w-3" />
                      </div>
                      <span className="font-semibold text-xs text-foreground">
                        {proposal.current_assignee_name || `Developer #${proposal.current_assignee_id}`}
                      </span>
                    </div>

                    {proposal.current_assignee_workload && (
                      <div className="text-[11px] text-muted-foreground pt-1">
                        Workload:{" "}
                        <strong className="text-red-500">
                          {proposal.current_assignee_workload.assigned_points} pts
                        </strong>{" "}
                        / {proposal.current_assignee_workload.capacity_points} cap (
                        {Math.round(proposal.current_assignee_workload.utilization_ratio * 100)}% utilization)
                      </div>
                    )}
                  </div>

                  {/* Proposed Assignee */}
                  <div className="p-3.5 rounded-lg bg-secondary/30 border border-border space-y-1.5">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase">
                      Proposed Assignee (Target)
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="h-6 w-6 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center font-bold text-xs">
                        <User className="h-3 w-3" />
                      </div>
                      <span className="font-semibold text-xs text-foreground">
                        {proposal.proposed_assignee_name || `Developer #${proposal.proposed_assignee_id}`}
                      </span>
                    </div>

                    {proposal.proposed_assignee_workload && (
                      <div className="text-[11px] text-muted-foreground pt-1 space-y-1">
                        <div>
                          Available capacity:{" "}
                          <strong className="text-emerald-500">
                            {proposal.proposed_assignee_workload.available_points} pts available
                          </strong>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {proposal.proposed_assignee_workload.skills.map((s) => (
                            <span
                              key={s}
                              className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-secondary-foreground border border-border"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons for Pending */}
                {isPending && (
                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
                    <button
                      onClick={() => rejectMutation.mutate({ id: proposal.id, reason: "Rejected by manager" })}
                      disabled={!isManager || rejectMutation.isPending}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-secondary border border-border text-foreground hover:bg-red-500/10 hover:text-red-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                      title={!isManager ? "Requires Manager role" : "Reject proposal"}
                    >
                      <X className="h-3.5 w-3.5" />
                      <span>Reject</span>
                    </button>

                    <button
                      onClick={() => approveMutation.mutate(proposal.id)}
                      disabled={!isManager || approveMutation.isPending}
                      className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-primary text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                      title={!isManager ? "Requires Manager role" : "Approve and execute reassignment"}
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>Approve & Reassign</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
