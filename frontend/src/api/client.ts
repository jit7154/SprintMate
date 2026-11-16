import type {
  AssistantQueryResponse,
  AuditLogEntry,
  BurndownPoint,
  Developer,
  Issue,
  Proposal,
  PullRequest,
  Sprint,
  SprintSummaryResponse,
  StandupResponse,
  UsageSummary,
  UserRole,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api";

let currentRole: UserRole = "manager";
let currentUserId = "manager-alex";

export function setApiAuth(role: UserRole, userId?: string) {
  currentRole = role;
  currentUserId = userId || (role === "manager" ? "manager-alex" : "dev-priya");
}

export function getApiAuth(): { role: UserRole; userId: string } {
  return { role: currentRole, userId: currentUserId };
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    "X-User-Role": currentRole,
    "X-User-Id": currentUserId,
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) errorDetail = errorJson.detail;
    } catch {
      // Ignore JSON parse failure
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Sprints
  getSprints: () => request<Sprint[]>("/sprints"),
  getActiveSprint: () => request<SprintSummaryResponse>("/sprints/active"),
  getSprintIssues: (sprintId?: number) => {
    const q = sprintId ? `?sprint_id=${sprintId}` : "";
    return request<Issue[]>(`/sprints/issues${q}`);
  },
  getBurndown: (sprintId: number) => request<BurndownPoint[]>(`/sprints/${sprintId}/burndown`),

  // Pull Requests
  getPullRequests: (params?: { stuck_only?: boolean; issue_key?: string }) => {
    const query = new URLSearchParams();
    if (params?.stuck_only) query.set("stuck_only", "true");
    if (params?.issue_key) query.set("issue_key", params.issue_key);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<PullRequest[]>(`/pull-requests${qs}`);
  },
  getPullRequest: (prNumber: number) => request<PullRequest>(`/pull-requests/${prNumber}`),

  // Team Workload
  getTeamDevelopers: () => request<Developer[]>("/team/developers"),

  // AI Assistant
  queryAssistant: (query: string, sprintId?: number) =>
    request<AssistantQueryResponse>("/assistant/query", {
      method: "POST",
      body: JSON.stringify({ query, sprint_id: sprintId }),
    }),
  getStandup: (sprintId?: number) => {
    const q = sprintId ? `?sprint_id=${sprintId}` : "";
    return request<StandupResponse>(`/assistant/standup${q}`);
  },

  // Proposals & Approvals
  getProposals: (status?: string) => {
    const q = status ? `?status=${status}` : "";
    return request<Proposal[]>(`/proposals${q}`);
  },
  createProposal: (data: { issue_key: string; proposed_assignee_id: number; reason: string }) =>
    request<Proposal>("/proposals", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  approveProposal: (proposalId: number) =>
    request<{ status: string; new_assignee_id: number; message: string }>(
      `/proposals/${proposalId}/approve`,
      { method: "POST" }
    ),
  rejectProposal: (proposalId: number, reason?: string) =>
    request<{ status: string; message: string }>(`/proposals/${proposalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ rejection_reason: reason }),
    }),

  // Audit Logs
  getAuditLogs: (params?: { entity_type?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.entity_type) query.set("entity_type", params.entity_type);
    if (params?.limit) query.set("limit", String(params.limit));
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<AuditLogEntry[]>(`/audit${qs}`);
  },

  // Usage & Telemetry
  getUsageSummary: () => request<UsageSummary>("/usage"),
};
