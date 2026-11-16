import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { Users, AlertTriangle, CheckCircle, ShieldCheck } from "lucide-react";

export const TeamPage: React.FC = () => {
  const { data: developers = [], isLoading } = useQuery({
    queryKey: ["teamDevelopers"],
    queryFn: () => api.getTeamDevelopers(),
  });

  return (
    <div className="space-y-6">
      <div className="bg-card border border-border p-6 rounded-xl shadow-xs">
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-primary" />
          <div>
            <h1 className="text-base font-bold text-foreground">Team Capacity & Workload Allocation</h1>
            <p className="text-xs text-muted-foreground">
              Tracking story points assigned vs. weekly capacity threshold (8 pts default)
            </p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {developers.map((dev) => {
            const utilPercent = Math.round(dev.utilization_ratio * 100);

            return (
              <div
                key={dev.id}
                className={`p-5 rounded-xl bg-card border transition-all ${
                  dev.is_overloaded
                    ? "border-red-500/50 bg-red-500/5 shadow-xs"
                    : "border-border hover:border-primary/40 shadow-xs"
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-foreground">{dev.name}</h3>
                    <p className="text-[11px] text-muted-foreground">{dev.role}</p>
                    <span className="inline-block mt-1 text-[10px] font-medium px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
                      {dev.team_name || `Team ${dev.team_id}`}
                    </span>
                  </div>

                  {dev.is_overloaded ? (
                    <span className="flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded bg-red-500/15 text-red-500 border border-red-500/30">
                      <AlertTriangle className="h-3 w-3" />
                      <span>OVERLOADED</span>
                    </span>
                  ) : (
                    <span className="flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">
                      <CheckCircle className="h-3 w-3" />
                      <span>HEALTHY</span>
                    </span>
                  )}
                </div>

                {/* Capacity Progress Bar */}
                <div className="mt-4 pt-3 border-t border-border">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">
                      Assigned: <strong className="text-foreground">{dev.assigned_points} pts</strong>
                    </span>
                    <span className="text-muted-foreground">
                      Cap: <strong className="text-foreground">{dev.weekly_capacity_points} pts</strong>
                    </span>
                  </div>

                  <div className="w-full bg-secondary rounded-full h-2 overflow-hidden flex">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        dev.is_overloaded
                          ? "bg-red-500"
                          : utilPercent > 80
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, (dev.assigned_points / (dev.weekly_capacity_points || 1)) * 100)}%` }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-[10px] mt-1.5 text-muted-foreground">
                    <span>Utilization: {utilPercent}%</span>
                    <span>
                      {dev.available_capacity_points > 0
                        ? `${dev.available_capacity_points} pts available`
                        : `${Math.abs(dev.available_capacity_points)} pts over capacity`}
                    </span>
                  </div>
                </div>

                {/* Skills Tags */}
                <div className="mt-4 pt-3 border-t border-border">
                  <span className="text-[10px] font-semibold text-muted-foreground uppercase">Skills:</span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {dev.skills.map((s) => (
                      <span
                        key={s}
                        className="text-[10px] font-medium px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Assigned Issue Keys */}
                {dev.assigned_issue_keys && dev.assigned_issue_keys.length > 0 && (
                  <div className="mt-3 flex items-center space-x-1 overflow-x-auto text-[10px] font-mono text-primary pt-2">
                    <span className="text-muted-foreground text-[9px] mr-1">Issues:</span>
                    {dev.assigned_issue_keys.map((k) => (
                      <span key={k} className="px-1 py-0.2 rounded bg-primary/10 border border-primary/20">
                        {k}
                      </span>
                    ))}
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
