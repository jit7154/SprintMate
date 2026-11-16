from mcp.server.mcpserver import MCPServer

from mcp_server.tools_github import (
    get_ci_status,
    get_pull_request,
    search_pull_requests,
)
from mcp_server.tools_jira import (
    get_issue,
    get_issue_history,
    get_sprint,
    propose_reassignment,
    search_issues,
)


def create_mcp_server() -> MCPServer:
    """Create and configure SprintMate MCP Server with typed inspection tools."""
    server = MCPServer("SprintMate MCP Server")

    # Jira issue tracking tools (read-only queries + proposal creation)
    server.tool()(search_issues)
    server.tool()(get_issue)
    server.tool()(get_sprint)
    server.tool()(get_issue_history)
    server.tool()(propose_reassignment)

    # GitHub version control tools (read-only PRs and CI checks)
    server.tool()(search_pull_requests)
    server.tool()(get_pull_request)
    server.tool()(get_ci_status)

    return server


server = create_mcp_server()


def main():
    """Run MCP server over standard input/output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
