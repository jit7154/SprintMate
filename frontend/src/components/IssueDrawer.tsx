import React from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../hooks/useAppContext";
import { formatSeverityBadge } from "../lib/utils";
import { X, Clock, AlertTriangle, Link2, User, Sparkles, CheckCircle2 } from "lucide-react";

export const IssueDrawer: React.FC = () => {
  const { selectedIssue, setSelectedIssue } = useApp();
  const navigate = useNavigate();

  if (!selectedIssue) return null;

  const handleAskCopilot = () => {
    setSelectedIssue(null);
    navigate(`/assistant?q=${encodeURIComponent(`Analyze blockers and risk for issue ${selectedIssue.key}`)}`);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-card border-l border-border h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-6 border-b border-border flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                {selectedIssue.key}
              </span>
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${formatSeverityBadge(
                  selectedIssue.priority
                )}`}
              >
                {selectedIssue.priority}
              </span>
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
                {selectedIssue.story_points} pts
              </span>
            </div>
            <h2 className="text-lg font-bold text-foreground mt-2">{selectedIssue.title}</h2>
          </div>
          <button
            onClick={() => setSelectedIssue(null)}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {/* Status Alert if Blocked or Overdue */}
          {selectedIssue.status === "BLOCKED" && (
            <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 flex items-start space-x-2.5">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold text-xs">Issue is Blocked</p>
                <p className="text-xs mt-0.5 text-red-500/90">
                  {selectedIssue.blocked_by && selectedIssue.blocked_by.length > 0
                    ? `Waiting on dependency: ${selectedIssue.blocked_by.join(", ")}`
                    : "Work is currently halted by an external blocker."}
                </p>
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Description
            </h3>
            <p className="text-foreground text-xs leading-relaxed bg-secondary/50 p-3 rounded-lg border border-border">
              {selectedIssue.description || "No description provided."}
            </p>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-secondary/40 p-3 rounded-lg border border-border">
              <span className="text-[10px] font-medium text-muted-foreground uppercase">Assignee</span>
              <div className="flex items-center space-x-2 mt-1">
                <div className="h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-xs">
                  <User className="h-3 w-3" />
                </div>
                <span className="font-medium text-foreground text-xs">
                  {selectedIssue.assignee_name || "Unassigned"}
                </span>
              </div>
            </div>

            <div className="bg-secondary/40 p-3 rounded-lg border border-border">
              <span className="text-[10px] font-medium text-muted-foreground uppercase">Due Date</span>
              <div className="flex items-center space-x-1.5 mt-1 text-xs">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                <span className={selectedIssue.is_overdue ? "text-red-500 font-semibold" : "text-foreground"}>
                  {selectedIssue.due_date ? new Date(selectedIssue.due_date).toLocaleDateString() : "No deadline"}
                </span>
              </div>
            </div>
          </div>

          {/* Dependencies */}
          {((selectedIssue.blocked_by && selectedIssue.blocked_by.length > 0) ||
            (selectedIssue.blocks && selectedIssue.blocks.length > 0)) && (
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center space-x-1">
                <Link2 className="h-3.5 w-3.5" />
                <span>Dependencies</span>
              </h3>
              <div className="space-y-2">
                {selectedIssue.blocked_by?.map((key) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded-md bg-secondary text-xs border border-border"
                  >
                    <span className="text-muted-foreground">Blocked by:</span>
                    <span className="font-mono font-bold text-red-500">{key}</span>
                  </div>
                ))}
                {selectedIssue.blocks?.map((key) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded-md bg-secondary text-xs border border-border"
                  >
                    <span className="text-muted-foreground">Blocks:</span>
                    <span className="font-mono font-bold text-amber-500">{key}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* History Timeline */}
          {selectedIssue.history && selectedIssue.history.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Audit Timeline
              </h3>
              <div className="relative pl-4 space-y-3 border-l-2 border-border ml-2 text-xs">
                {selectedIssue.history.map((h, i) => (
                  <div key={i} className="relative">
                    <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-primary" />
                    <p className="font-medium text-foreground">
                      {h.field_name}:{" "}
                      <span className="line-through text-muted-foreground">{h.old_value || "None"}</span> →{" "}
                      <span className="font-bold text-primary">{h.new_value}</span>
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      by {h.changed_by} • {new Date(h.changed_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer Action */}
        <div className="p-4 border-t border-border bg-card flex space-x-2">
          <button
            onClick={handleAskCopilot}
            className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-xs shadow-sm hover:opacity-90 transition-opacity"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Investigate with AI Copilot</span>
          </button>
        </div>
      </div>
    </div>
  );
};
