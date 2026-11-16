export type UserRole = "manager" | "developer";

export interface Sprint {
  id: number;
  name: string;
  status: "ACTIVE" | "COMPLETED" | "PLANNED";
  start_date: string;
  end_date: string;
  sprint_goal: string;
  total_days: number;
  days_elapsed: number;
}

export interface IssueHistory {
  id: number;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  changed_by: string;
  changed_at: string;
}

export interface Issue {
  id: number;
  key: string;
  title: string;
  description: string;
  status: "TO_DO" | "IN_PROGRESS" | "IN_REVIEW" | "DONE" | "BLOCKED";
  story_points: number;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  sprint_id: number;
  assignee_id: number | null;
  assignee_name?: string | null;
  due_date: string | null;
  labels: string[];
  blocked_by?: string[];
  blocks?: string[];
  history?: IssueHistory[];
  is_overdue?: boolean;
  days_overdue?: number;
  days_blocked?: number;
}

export interface CiRun {
  id: number;
  pr_id: number;
  commit_hash: string;
  status: "SUCCESS" | "FAILURE" | "RUNNING" | "PENDING";
  failed_step: string | null;
  run_duration_seconds: number;
  run_completed_at: string;
}

export interface PullRequest {
  id: number;
  pr_number: number;
  repo: string;
  title: string;
  branch: string;
  status: "OPEN" | "MERGED" | "CLOSED";
  review_status: "PENDING_REVIEW" | "APPROVED" | "CHANGES_REQUESTED";
  issue_key: string | null;
  author_id: number;
  author_name?: string | null;
  requested_reviewers: string[];
  pr_created_at: string;
  pr_updated_at: string;
  is_stuck?: boolean;
  age_days?: number;
  latest_ci_status?: "SUCCESS" | "FAILURE" | "RUNNING" | "PENDING" | null;
  latest_ci_step?: string | null;
  ci_runs?: CiRun[];
}

export interface Developer {
  id: number;
  name: string;
  email: string;
  role: string;
  team_id: number;
  team_name?: string;
  skills: string[];
  weekly_capacity_points: number;
  assigned_points: number;
  assigned_issues_count: number;
  assigned_issue_keys: string[];
  available_capacity_points: number;
  utilization_ratio: number;
  is_overloaded: boolean;
}

export interface RiskFinding {
  rule_id: string;
  rule_name: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  weight: number;
  affected_keys: string[];
  reason: string;
  metadata: Record<string, any>;
}

export interface RiskBreakdown {
  category: string;
  category_name: string;
  points: number;
  findings_count: number;
}

export interface RiskEvaluation {
  sprint_id: number;
  sprint_name: string;
  overall_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  explanation: string;
  breakdown: RiskBreakdown[];
  top_risks: RiskFinding[];
  evaluated_at: string;
  blocked_issues_count: number;
  overdue_issues_count: number;
  stuck_prs_count: number;
  overloaded_devs_count: number;
}

export interface SprintSummaryResponse {
  sprint: Sprint;
  total_issues: number;
  completed_issues: number;
  in_progress_issues: number;
  blocked_issues: number;
  total_points: number;
  completed_points: number;
  risk_evaluation: RiskEvaluation;
}

export interface BurndownPoint {
  day: string;
  ideal: number;
  actual: number | null;
}

export interface Proposal {
  id: number;
  issue_key: string;
  current_assignee_id: number | null;
  current_assignee_name?: string | null;
  current_assignee_workload?: {
    assigned_points: number;
    capacity_points: number;
    utilization_ratio: number;
    is_overloaded: boolean;
  };
  proposed_assignee_id: number;
  proposed_assignee_name?: string | null;
  proposed_assignee_workload?: {
    assigned_points: number;
    capacity_points: number;
    available_points: number;
    skills: string[];
  };
  reason: string;
  status: "PENDING" | "EXECUTED" | "REJECTED" | "STALE";
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogEntry {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string;
  actor_role: string;
  before_state: Record<string, any> | null;
  after_state: Record<string, any> | null;
  outcome: string;
  timestamp: string;
}

export interface UsageRecord {
  id: number;
  request_id: string;
  query: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  tools_called: string[];
  agent_path: string[];
  created_at: string;
}

export interface UsageSummary {
  total_investigations: number;
  average_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_estimated_cost_usd: number;
  records: UsageRecord[];
}

export interface EvidenceItem {
  type: string;
  key: string;
  url?: string;
}

export interface AssistantQueryResponse {
  answer: string;
  evidence: EvidenceItem[];
  tools_called: string[];
  agent_path: string[];
  latency_ms: number;
  tokens_used: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
}

export interface StandupResponse {
  sprint_name: string;
  generated_at: string;
  completed: any[];
  in_progress: any[];
  blockers: any[];
  delayed: any[];
  pending_reviews: any[];
  discussion_points: string[];
  ai_summary: string;
}
