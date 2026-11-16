import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useApp } from "../hooks/useAppContext";
import type { AssistantQueryResponse } from "../types";
import {
  BotMessageSquare,
  Sparkles,
  Send,
  Cpu,
  Clock,
  Coins,
  ChevronDown,
  ChevronUp,
  FileText,
  AlertCircle,
  CheckCircle2,
  ListTodo,
} from "lucide-react";

const SUGGESTED_PROMPTS = [
  "Why is Sprint 24 at high risk?",
  "Which pull requests are stuck in CI build failures?",
  "Analyze bottlenecks blocking PAY-142 and propose reassignment",
  "Generate daily standup briefing for Sprint 24",
];

export const AssistantPage: React.FC = () => {
  const { selectedSprintId, setSelectedIssue } = useApp();
  const location = useLocation();

  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState<
    {
      id: string;
      sender: "user" | "assistant";
      text: string;
      response?: AssistantQueryResponse;
      timestamp: Date;
    }[]
  >([]);

  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "standup">("chat");

  const queryMutation = useMutation({
    mutationFn: (q: string) => api.queryAssistant(q, selectedSprintId),
    onSuccess: (data, q) => {
      const assistantMsg = {
        id: `ast-${Date.now()}`,
        sender: "assistant" as const,
        text: data.answer,
        response: data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setExpandedTraceId(assistantMsg.id); // Expand telemetry drawer
    },
    onError: (err: any) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `ast-${Date.now()}`,
          sender: "assistant",
          text: `Error during agent investigation: ${err.message}`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const { data: standup, isLoading: isStandupLoading, refetch: refetchStandup } = useQuery({
    queryKey: ["standup", selectedSprintId],
    queryFn: () => api.getStandup(selectedSprintId),
    enabled: activeTab === "standup",
  });

  // Handle URL query parameter ?q=...
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get("q");
    if (q) {
      handleSend(q);
    }
  }, [location.search]);

  const handleSend = (textToSend?: string) => {
    const q = (textToSend || inputQuery).trim();
    if (!q || queryMutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      {
        id: `usr-${Date.now()}`,
        sender: "user",
        text: q,
        timestamp: new Date(),
      },
    ]);

    setInputQuery("");
    queryMutation.mutate(q);
  };

  const handleEvidenceClick = (key: string) => {
    if (key.startsWith("PR #") || key.startsWith("PR ")) return;
    api.getSprintIssues(selectedSprintId).then((issues) => {
      const issue = issues.find((i) => i.key === key);
      if (issue) setSelectedIssue(issue);
    });
  };

  return (
    <div className="space-y-4">
      {/* Tab Switcher */}
      <div className="flex items-center space-x-2 border-b border-border pb-2">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === "chat"
              ? "bg-primary text-primary-foreground shadow-xs"
              : "text-muted-foreground hover:bg-secondary hover:text-foreground"
          }`}
        >
          <BotMessageSquare className="h-3.5 w-3.5" />
          <span>Interactive Copilot</span>
        </button>
        <button
          onClick={() => setActiveTab("standup")}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === "standup"
              ? "bg-primary text-primary-foreground shadow-xs"
              : "text-muted-foreground hover:bg-secondary hover:text-foreground"
          }`}
        >
          <ListTodo className="h-3.5 w-3.5" />
          <span>Automated Standup Briefing</span>
        </button>
      </div>

      {activeTab === "chat" ? (
        <div className="flex flex-col h-[750px] bg-card border border-border rounded-xl shadow-xs overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-border bg-secondary/30 flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="h-7 w-7 rounded-lg bg-primary/20 text-primary flex items-center justify-center">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-xs font-bold text-foreground">DevCore AI Sprint Copilot</h2>
                <p className="text-[10px] text-muted-foreground">
                  Orchestrated by Google ADK Supervisor + Investigator MCP agent
                </p>
              </div>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <BotMessageSquare className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-foreground">How can I assist your sprint?</h3>
                  <p className="text-xs text-muted-foreground max-w-sm mt-1">
                    I correlate Jira issues, GitHub pull requests, CI test step failures, and developer workloads.
                  </p>
                </div>

                {/* Suggested Prompt Chips */}
                <div className="flex flex-wrap gap-2 justify-center max-w-lg mt-2">
                  {SUGGESTED_PROMPTS.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(prompt)}
                      className="text-xs px-3 py-1.5 rounded-full bg-secondary border border-border text-foreground hover:border-primary/50 hover:bg-secondary/80 transition-all text-left"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-2xl p-4 rounded-xl text-xs space-y-2 ${
                    msg.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary/60 border border-border text-foreground"
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-line">{msg.text}</p>

                  {/* Evidence Items Chips */}
                  {msg.response?.evidence && msg.response.evidence.length > 0 && (
                    <div className="pt-2 border-t border-border/50 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                        Evidence:
                      </span>
                      {msg.response.evidence.map((ev, i) => (
                        <button
                          key={i}
                          onClick={() => handleEvidenceClick(ev.key)}
                          className="px-2 py-0.5 rounded bg-primary/15 text-primary border border-primary/25 font-mono text-[10px] hover:bg-primary/25 transition-colors cursor-pointer"
                          title="Click to view details in drawer"
                        >
                          {ev.key}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Expandable "How I answered" Telemetry Drawer */}
                {msg.response && (
                  <div className="mt-1.5 max-w-2xl w-full">
                    <button
                      onClick={() =>
                        setExpandedTraceId(expandedTraceId === msg.id ? null : msg.id)
                      }
                      className="flex items-center space-x-1 text-[10px] font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <span>How I answered (Telemetry & Multi-Agent Trace)</span>
                      {expandedTraceId === msg.id ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                    </button>

                    {expandedTraceId === msg.id && (
                      <div className="mt-2 p-3 rounded-lg bg-card border border-border text-[11px] space-y-2.5 animate-in fade-in duration-150">
                        <div className="grid grid-cols-4 gap-2 text-center">
                          <div className="p-1.5 rounded bg-secondary/50">
                            <span className="text-[9px] text-muted-foreground uppercase">Latency</span>
                            <p className="font-bold font-mono text-foreground">{msg.response.latency_ms} ms</p>
                          </div>
                          <div className="p-1.5 rounded bg-secondary/50">
                            <span className="text-[9px] text-muted-foreground uppercase">Input Tokens</span>
                            <p className="font-bold font-mono text-foreground">
                              {msg.response.tokens_used.input_tokens}
                            </p>
                          </div>
                          <div className="p-1.5 rounded bg-secondary/50">
                            <span className="text-[9px] text-muted-foreground uppercase">Output Tokens</span>
                            <p className="font-bold font-mono text-foreground">
                              {msg.response.tokens_used.output_tokens}
                            </p>
                          </div>
                          <div className="p-1.5 rounded bg-secondary/50">
                            <span className="text-[9px] text-muted-foreground uppercase">Estimated Cost</span>
                            <p className="font-bold font-mono text-emerald-500">
                              ${msg.response.tokens_used.estimated_cost_usd.toFixed(6)}
                            </p>
                          </div>
                        </div>

                        {/* MCP Tools Called */}
                        <div>
                          <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                            MCP Tools Executed:
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {msg.response.tools_called.map((tool, idx) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono text-[10px] border border-border"
                              >
                                {tool}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Agent Path */}
                        <div>
                          <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                            Agent Execution Path:
                          </span>
                          <div className="flex items-center space-x-1.5 mt-1 font-mono text-[10px] text-primary">
                            {msg.response.agent_path.map((agent, idx) => (
                              <React.Fragment key={idx}>
                                {idx > 0 && <span className="text-muted-foreground">→</span>}
                                <span className="px-1.5 py-0.5 rounded bg-primary/10 border border-primary/20">
                                  {agent}
                                </span>
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {queryMutation.isPending && (
              <div className="flex items-center space-x-2 text-xs text-muted-foreground p-3 rounded-lg bg-secondary/30 w-fit">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary"></div>
                <span>Supervisor is invoking Investigator via stdio MCP tools...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="p-3 border-t border-border bg-card">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                placeholder="Ask about sprint risks, blocked tickets, CI failures, or reassignments..."
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={queryMutation.isPending}
                className="flex-1 bg-secondary text-xs rounded-lg px-3.5 py-2.5 border border-border focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={queryMutation.isPending || !inputQuery.trim()}
                className="p-2.5 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Standup Briefing View */
        <div className="bg-card border border-border rounded-xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <div>
              <h2 className="text-base font-bold text-foreground">
                Automated Daily Standup Briefing — {standup?.sprint_name || "Sprint 24"}
              </h2>
              <p className="text-xs text-muted-foreground">
                Correlating completed issues, active blockers, overdue PR reviews, and AI synthesis
              </p>
            </div>
            <button
              onClick={() => refetchStandup()}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-secondary border border-border hover:bg-secondary/80 text-foreground"
            >
              Refresh Briefing
            </button>
          </div>

          {isStandupLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : standup ? (
            <div className="space-y-6 text-xs">
              {/* Executive Summary */}
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 space-y-1.5">
                <div className="flex items-center space-x-1.5 font-bold text-primary">
                  <Sparkles className="h-4 w-4" />
                  <span>Executive AI Synthesis</span>
                </div>
                <p className="text-foreground leading-relaxed whitespace-pre-line">{standup.ai_summary}</p>
              </div>

              {/* Discussion Points */}
              <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-2">
                <span className="font-bold text-amber-500 uppercase tracking-wider text-[10px]">
                  Recommended Discussion Points for Standup:
                </span>
                <ul className="space-y-1 list-disc list-inside text-foreground">
                  {standup.discussion_points.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              </div>

              {/* Grid of Sections */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Blockers */}
                <div className="p-4 rounded-lg bg-secondary/40 border border-border space-y-2">
                  <h4 className="font-bold text-red-500 uppercase text-[10px]">
                    Active Blockers ({standup.blockers.length})
                  </h4>
                  {standup.blockers.map((b: any) => (
                    <div key={b.key} className="p-2 rounded bg-card border border-border space-y-0.5">
                      <span className="font-mono font-bold text-primary">{b.key}</span>
                      <p className="text-foreground font-medium">{b.title}</p>
                      <p className="text-muted-foreground text-[10px]">Assignee: {b.assignee_name}</p>
                    </div>
                  ))}
                </div>

                {/* Delayed / Overdue */}
                <div className="p-4 rounded-lg bg-secondary/40 border border-border space-y-2">
                  <h4 className="font-bold text-amber-500 uppercase text-[10px]">
                    Overdue / Delayed ({standup.delayed.length})
                  </h4>
                  {standup.delayed.map((d: any) => (
                    <div key={d.key} className="p-2 rounded bg-card border border-border space-y-0.5">
                      <span className="font-mono font-bold text-primary">{d.key}</span>
                      <p className="text-foreground font-medium">{d.title}</p>
                      <p className="text-red-500 text-[10px] font-semibold">{d.reason}</p>
                    </div>
                  ))}
                </div>

                {/* Pending PR Reviews */}
                <div className="p-4 rounded-lg bg-secondary/40 border border-border space-y-2">
                  <h4 className="font-bold text-blue-500 uppercase text-[10px]">
                    Stagnant PR Reviews ({standup.pending_reviews.length})
                  </h4>
                  {standup.pending_reviews.map((p: any) => (
                    <div key={p.pr_number} className="p-2 rounded bg-card border border-border space-y-0.5">
                      <span className="font-mono font-bold text-foreground">PR #{p.pr_number}</span>
                      <p className="text-foreground font-medium">{p.title}</p>
                      <p className="text-muted-foreground text-[10px]">
                        Waiting {p.age_days}d • Author: {p.author_name}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
