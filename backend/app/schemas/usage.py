from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsageRecordRead(BaseModel):
    id: int
    request_id: str
    query: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    tools_called: list[str]
    agent_path: list[str]
    errors_and_retries: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageSummary(BaseModel):
    total_investigations: int
    average_latency_ms: float
    p95_latency_ms: float
    average_cost_usd: float
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    records: list[UsageRecordRead]
