import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    StdioServerParameters,
)

from app.config import settings

INVESTIGATOR_INSTRUCTION = """
You are the DevCore Investigator Agent, a deep-dive forensic engineering assistant.
Your responsibility is to investigate sprint risks, pull requests, dependencies, and developer workloads.

Rules:
1. Use the provided MCP tools to look up ground-truth facts:
   - `get_sprint`: Find active sprint status, goals, and timeline.
   - `search_issues` & `get_issue`: Inspect issue status, story points, assignee, dependencies, and history.
   - `search_pull_requests` & `get_pull_request`: Check PR ages, review status, and branch information.
   - `get_ci_status`: Verify test failures and specific broken steps.
   - `propose_reassignment`: When a developer is overloaded (e.g. David Kim) or an issue is blocked, propose reassigning to an engineer with matching skills and free capacity (e.g. Rachel Green).
2. Every claim must cite concrete keys:
   - Issue keys: e.g. `PAY-142`, `PAY-139`, `PAY-150`, `CORE-108`.
   - PR numbers: e.g. `PR #204`, `PR #211`.
3. If evidence is missing or uncertain, explicitly state that evidence is unavailable.
4. Keep findings precise, structured, and factual. Avoid vague speculation.
"""


def create_mcp_toolset() -> McpToolset:
    """Create an ADK McpToolset connecting to the stdio MCP server."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "mcp_server.server"],
                cwd=str(backend_dir),
            )
        )
    )


def create_investigator_agent(toolset: McpToolset | None = None) -> LlmAgent:
    """Construct the Investigator sub-agent with MCP inspection tools."""
    active_toolset = toolset or create_mcp_toolset()
    return LlmAgent(
        name="investigator",
        model=settings.gemini_model,
        instruction=INVESTIGATOR_INSTRUCTION,
        tools=[active_toolset],
    )
