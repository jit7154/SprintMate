-- Initial database schema for SprintMate

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    mission VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS developers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    weekly_capacity_points INTEGER NOT NULL DEFAULT 8
);

CREATE TABLE IF NOT EXISTS sprints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    sprint_goal TEXT NOT NULL,
    total_days INTEGER NOT NULL DEFAULT 10,
    days_elapsed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);

CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    key VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(30) NOT NULL,
    story_points INTEGER NOT NULL DEFAULT 3,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    sprint_id INTEGER NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    assignee_id INTEGER REFERENCES developers(id) ON DELETE SET NULL,
    due_date TIMESTAMP,
    labels JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_issues_key ON issues(key);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_sprint_id ON issues(sprint_id);
CREATE INDEX IF NOT EXISTS idx_issues_assignee_id ON issues(assignee_id);

CREATE TABLE IF NOT EXISTS issue_dependencies (
    id SERIAL PRIMARY KEY,
    blocker_issue_key VARCHAR(20) NOT NULL,
    blocked_issue_key VARCHAR(20) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'blocks'
);
CREATE INDEX IF NOT EXISTS idx_deps_blocker ON issue_dependencies(blocker_issue_key);
CREATE INDEX IF NOT EXISTS idx_deps_blocked ON issue_dependencies(blocked_issue_key);

CREATE TABLE IF NOT EXISTS issue_history (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL,
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    changed_by VARCHAR(100) NOT NULL DEFAULT 'System',
    changed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_history_issue_id ON issue_history(issue_id);

CREATE TABLE IF NOT EXISTS pull_requests (
    id SERIAL PRIMARY KEY,
    pr_number INTEGER UNIQUE NOT NULL,
    repo VARCHAR(100) NOT NULL DEFAULT 'DevCore/monorepo',
    title VARCHAR(255) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    review_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    issue_key VARCHAR(20),
    author_id INTEGER NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    requested_reviewers JSONB NOT NULL DEFAULT '[]'::jsonb,
    pr_created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    pr_updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pr_number ON pull_requests(pr_number);
CREATE INDEX IF NOT EXISTS idx_pr_issue_key ON pull_requests(issue_key);

CREATE TABLE IF NOT EXISTS ci_runs (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    commit_hash VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL,
    failed_step VARCHAR(100),
    run_duration_seconds INTEGER NOT NULL DEFAULT 120,
    run_completed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ci_pr_id ON ci_runs(pr_id);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    service VARCHAR(100) NOT NULL,
    date VARCHAR(20) NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposals (
    id SERIAL PRIMARY KEY,
    issue_key VARCHAR(20) NOT NULL,
    current_assignee_id INTEGER,
    proposed_assignee_id INTEGER NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_by VARCHAR(100) NOT NULL DEFAULT 'InvestigatorAgent',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_issue_key ON proposals(issue_key);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    actor_role VARCHAR(50) NOT NULL,
    before_state JSONB,
    after_state JSONB,
    outcome VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

CREATE TABLE IF NOT EXISTS usage_records (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    latency_ms FLOAT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    tools_called JSONB NOT NULL DEFAULT '[]'::jsonb,
    agent_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    errors_and_retries JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_records(created_at);
