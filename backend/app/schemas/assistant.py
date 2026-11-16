from pydantic import BaseModel


class EvidenceReference(BaseModel):
    kind: str  # "issue", "pr", "risk_rule"
    key: str  # "PAY-142", "PR #204", "RULE_BLOCKED_ISSUE"
    summary: str


class ToolCallLog(BaseModel):
    tool_name: str
    arguments: dict
    result_preview: str


class AssistantQueryRequest(BaseModel):
    query: str
    sprint_id: int | None = None


class AssistantQueryResponse(BaseModel):
    answer: str
    evidence: list[EvidenceReference]
    tools_called: list[ToolCallLog]
    risk_rules_used: list[str]
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
