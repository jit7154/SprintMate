import re
import time
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.investigator import create_investigator_agent, create_mcp_toolset
from app.config import settings
from app.schemas.assistant import (
    AssistantQueryResponse,
    EvidenceReference,
    ToolCallLog,
)
from app.services.observability.usage_logger import (
    estimate_gemini_cost,
    log_agent_usage,
)

SUPERVISOR_INSTRUCTION = """
You are the DevCore Supervisor Agent, an AI partner for engineering managers.
You lead investigations into sprint risks, bottlenecks, developer capacity, and delivery threats.

Responsibilities:
1. Interpret the manager's query and identify the core technical risk questions.
2. Delegate forensic research to your sub-agent `investigator`, who has direct access to MCP tools (Jira issues, PRs, CI results).
3. Synthesize the investigator's findings into a crisp, high-signal response.
4. Formatting rules:
   - Use clear markdown with sections: **Executive Summary**, **Key Evidence & Root Causes**, and **Actionable Recommendations**.
   - Always reference concrete issue keys (e.g. `PAY-142`), PR numbers (e.g. `PR #204`), and developers by name.
   - If an issue or PR should be reassigned or prioritized, explain why based on developer skills and capacity.
"""


def create_supervisor_agent(investigator: LlmAgent | None = None) -> LlmAgent:
    """Construct the Supervisor root agent with the Investigator sub-agent."""
    sub_agent = investigator or create_investigator_agent()
    return LlmAgent(
        name="supervisor",
        model=settings.gemini_model,
        instruction=SUPERVISOR_INSTRUCTION,
        sub_agents=[sub_agent],
    )


def extract_evidence(text: str) -> list[EvidenceReference]:
    """Scan text for mentioned issue keys and PR numbers to build evidence chips."""
    evidence = []
    seen = set()

    # Match issue keys: CORE-101, PAY-142, CX-201
    for match in re.finditer(r"\b([A-Z]{2,10}-\d+)\b", text):
        key = match.group(1)
        if key not in seen:
            seen.add(key)
            evidence.append(
                EvidenceReference(
                    kind="issue",
                    key=key,
                    summary=f"Issue {key} referenced in investigation analysis",
                )
            )

    # Match PR numbers: PR #204, PR 211
    for match in re.finditer(r"\bPR\s*#?(\d+)\b", text, re.IGNORECASE):
        pr_num = f"PR #{match.group(1)}"
        if pr_num not in seen:
            seen.add(pr_num)
            evidence.append(
                EvidenceReference(
                    kind="pr",
                    key=pr_num,
                    summary=f"Pull Request #{match.group(1)} cited in investigation findings",
                )
            )

    return evidence


async def run_investigation(
    query: str,
    session: AsyncSession,
    sprint_id: int | None = None,
) -> AssistantQueryResponse:
    """Execute multi-agent investigation workflow over stdio MCP tools with usage tracking."""
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    toolset = create_mcp_toolset()
    investigator = create_investigator_agent(toolset)
    supervisor = create_supervisor_agent(investigator)

    session_service = InMemorySessionService()
    app_name = f"sprintmate-{request_id}"
    user_id = "manager-user"
    session_id = f"session-{request_id}"

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        agent=supervisor,
        session_service=session_service,
        app_name=app_name,
    )

    prompt = query
    if sprint_id:
        prompt = f"[Target Sprint ID: {sprint_id}] {query}"

    message = types.Content(parts=[types.Part.from_text(text=prompt)])

    text_parts: list[str] = []
    tools_called: list[ToolCallLog] = []
    tool_names: list[str] = []
    agent_path: list[str] = []
    input_tokens = 0
    output_tokens = 0
    errors: list[str] = []

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if event.author and (not agent_path or agent_path[-1] != event.author):
                agent_path.append(event.author)

            # Collect token usage if provided in event
            if hasattr(event, "usage_metadata") and event.usage_metadata:
                input_tokens += (
                    getattr(event.usage_metadata, "prompt_token_count", 0) or 0
                )
                output_tokens += (
                    getattr(event.usage_metadata, "candidates_token_count", 0) or 0
                )

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text_parts.append(part.text)
                    elif part.function_call:
                        call = part.function_call
                        t_name = call.name or "unknown"
                        t_args = dict(call.args) if call.args else {}
                        tool_names.append(t_name)
                        tools_called.append(
                            ToolCallLog(
                                tool_name=t_name,
                                arguments=t_args,
                                result_preview=f"Called {t_name} with {list(t_args.keys())}",
                            )
                        )
    except Exception as e:
        errors.append(str(e))
        text_parts.append(f"\n\n*Error during investigation execution: {e}*")
    finally:
        await toolset.close()

    latency_ms = (time.perf_counter() - start_time) * 1000
    answer = "".join(text_parts).strip()
    if not answer:
        answer = (
            "Investigation completed. No anomalies identified for the given criteria."
        )

    evidence = extract_evidence(answer)

    # Estimate tokens if runner didn't provide usage metadata directly
    if input_tokens == 0:
        input_tokens = len(query.split()) * 4 + 450
    if output_tokens == 0:
        output_tokens = len(answer.split()) * 4

    cost = estimate_gemini_cost(input_tokens, output_tokens)

    # Identify risk rules used in findings
    risk_rules_used = []
    if "blocked" in answer.lower():
        risk_rules_used.append("RULE_BLOCKED_ISSUE")
    if "overdue" in answer.lower() or "due" in answer.lower():
        risk_rules_used.append("RULE_OVERDUE_ISSUE")
    if "pr" in answer.lower() and "review" in answer.lower():
        risk_rules_used.append("RULE_PR_NO_REVIEW")
    if "ci" in answer.lower() or "fail" in answer.lower():
        risk_rules_used.append("RULE_PR_FAILING_CI")
    if "overload" in answer.lower() or "capacity" in answer.lower():
        risk_rules_used.append("RULE_DEVELOPER_OVERLOAD")
    if "depend" in answer.lower():
        risk_rules_used.append("RULE_DEPENDENCY_CHAIN")

    # Persist usage telemetry to database
    await log_agent_usage(
        session=session,
        request_id=request_id,
        query=query,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        tools_called=tool_names,
        agent_path=agent_path,
        errors_and_retries=errors,
    )

    return AssistantQueryResponse(
        answer=answer,
        evidence=evidence,
        tools_called=tools_called,
        risk_rules_used=risk_rules_used,
        latency_ms=round(latency_ms, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=cost,
    )
