from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters


root_agent = Agent(
    name="adk_mcp_smart_agent",
    model="gemini-2.0-flash",
    description="An ADK agent that connects to a custom MCP server and uses MCP tools.",
    instruction="""
You are an intelligent ADK agent connected to a custom MCP server.

You can use MCP tools to:
1. Add numbers
2. Subtract numbers
3. Multiply numbers
4. Get student details
5. Create project plans
6. Generate study schedules
7. Answer basic questions

Rules:
- Understand the user's request.
- Use the correct MCP tool whenever possible.
- If the user asks math, use the math tools.
- If the user asks for student details, use get_student_details.
- If the user asks for a project plan, use create_project_plan.
- If the user asks for a study schedule, use generate_study_schedule.
- If the user asks a general question about MCP, AI, Python, API, tools, server, client, or venv, use answer_user_question.
- Give a clear final answer after using a tool.
""",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=["server.py"],
            )
        )
    ],
)