import os
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ============================================================
# APP CONFIG
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.35
MAX_TOKENS = 1200  # Display only. Not passed directly for compatibility.

app = FastAPI(
    title="SPI Multi-Team Agentic AI",
    description="Local AutoGen-powered multi-team agentic AI web app with tools and backend overview.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")


# ============================================================
# MEMORY / BACKEND STATE
# ============================================================

chat_history: List[Dict[str, Any]] = []
backend_events: List[Dict[str, Any]] = []
team_runs: List[Dict[str, Any]] = []

stats: Dict[str, Any] = {
    "app_name": "SPI Multi-Team Agentic AI",
    "status": "online",
    "model": MODEL_NAME,
    "temperature": TEMPERATURE,
    "max_tokens": MAX_TOKENS,

    "total_requests": 0,
    "total_tool_calls": 0,
    "total_team_runs": 0,

    "last_response_time_seconds": 0,

    "estimated_total_input_chars": 0,
    "estimated_total_output_chars": 0,
    "estimated_total_tokens": 0,

    "last_prompt_tokens": 0,
    "last_completion_tokens": 0,
    "last_total_tokens": 0,
    "last_inner_messages": 0,

    "last_active_teams": [],
    "last_team_flow": [],

    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}


teams_overview: List[Dict[str, Any]] = [
    {
        "team_id": "planning_team",
        "team_name": "Planning Team",
        "team_type": "RoundRobinGroupChat",
        "status": "ready",
        "purpose": "Understands the user request, breaks it into clear steps, and decides what should happen next.",
        "agents": [
            {
                "name": "Planner_Agent",
                "role": "Creates a clear plan for the user task.",
            },
            {
                "name": "Task_Analyst_Agent",
                "role": "Analyzes requirements, risks, missing details, and task type.",
            },
        ],
        "works_with": [
            "user message",
            "task requirements",
            "planning decisions",
            "next-step instructions",
        ],
        "last_work": "Waiting for task.",
    },
    {
        "team_id": "tool_team",
        "team_name": "Tool Team",
        "team_type": "RoundRobinGroupChat",
        "status": "ready",
        "purpose": "Uses tools when needed, such as calculator, weather, studio info, chat summary, and task planning.",
        "agents": [
            {
                "name": "Tool_Agent",
                "role": "Decides and uses available tools.",
            },
        ],
        "works_with": [
            "calculator tool",
            "weather tool",
            "studio info tool",
            "chat summary tool",
            "task planner tool",
        ],
        "last_work": "Waiting for tool request.",
    },
    {
        "team_id": "review_team",
        "team_name": "Review Team",
        "team_type": "RoundRobinGroupChat",
        "status": "ready",
        "purpose": "Reviews the plan/tool output and creates a clean final answer for the user.",
        "agents": [
            {
                "name": "Reviewer_Agent",
                "role": "Checks if the answer is correct, useful, and complete.",
            },
            {
                "name": "Final_Response_Agent",
                "role": "Writes the final user-facing answer.",
            },
        ],
        "works_with": [
            "planning output",
            "tool output",
            "review notes",
            "final response",
        ],
        "last_work": "Waiting for review.",
    },
]


def now_time() -> str:
    return time.strftime("%H:%M:%S")


def add_event(
    event_type: str,
    content: str = "",
    tool: str = "",
    input_data: str = "",
    output_data: str = "",
    team: str = "",
    agent: str = "",
):
    backend_events.append(
        {
            "type": event_type,
            "team": team,
            "agent": agent,
            "tool": tool,
            "input": input_data,
            "output": output_data,
            "content": content,
            "time": now_time(),
        }
    )

    if len(backend_events) > 220:
        del backend_events[:100]


def estimate_tokens() -> int:
    total_chars = (
        stats["estimated_total_input_chars"]
        + stats["estimated_total_output_chars"]
    )

    return total_chars // 4


def update_team_status(team_id: str, status: str, last_work: str):
    for team in teams_overview:
        if team["team_id"] == team_id:
            team["status"] = status
            team["last_work"] = last_work
            break


def reset_team_statuses():
    for team in teams_overview:
        team["status"] = "ready"
        if team["team_id"] == "planning_team":
            team["last_work"] = "Waiting for task."
        elif team["team_id"] == "tool_team":
            team["last_work"] = "Waiting for tool request."
        elif team["team_id"] == "review_team":
            team["last_work"] = "Waiting for review."


# ============================================================
# SIMPLE TOOLS
# ============================================================

def calculator(expression: str) -> str:
    """
    Calculate simple math expressions.
    Example: 10 + 5 * 2
    """
    stats["total_tool_calls"] += 1

    add_event(
        event_type="tool_call",
        team="Tool Team",
        agent="Tool_Agent",
        tool="calculator",
        input_data=expression,
    )

    try:
        allowed_chars = "0123456789+-*/(). "

        if not all(char in allowed_chars for char in expression):
            result = "Invalid expression. Only numbers and + - * / ( ) are allowed."

            add_event(
                event_type="tool_result",
                team="Tool Team",
                agent="Tool_Agent",
                tool="calculator",
                output_data=result,
            )

            return result

        answer = eval(expression)

        result = f"The answer is {answer}"

        add_event(
            event_type="tool_result",
            team="Tool Team",
            agent="Tool_Agent",
            tool="calculator",
            output_data=result,
        )

        return result

    except Exception as e:
        error = f"Calculator error: {str(e)}"

        add_event(
            event_type="tool_error",
            team="Tool Team",
            agent="Tool_Agent",
            tool="calculator",
            output_data=error,
        )

        return error


def get_studio_info() -> str:
    """
    Gives information about Stellar Pulse Interactive.
    """
    stats["total_tool_calls"] += 1

    add_event(
        event_type="tool_call",
        team="Tool Team",
        agent="Tool_Agent",
        tool="get_studio_info",
        input_data="studio info requested",
    )

    result = (
        "The studio name is Stellar Pulse Interactive. "
        "It focuses on games, web apps, AI tools, automation, and creative software projects."
    )

    add_event(
        event_type="tool_result",
        team="Tool Team",
        agent="Tool_Agent",
        tool="get_studio_info",
        output_data=result,
    )

    return result


def create_task_plan(goal: str) -> str:
    """
    Break a user goal into simple practical steps.
    """
    stats["total_tool_calls"] += 1

    add_event(
        event_type="tool_call",
        team="Tool Team",
        agent="Tool_Agent",
        tool="create_task_plan",
        input_data=goal,
    )

    result = f"""
Task plan for: {goal}

1. Understand the goal clearly.
2. Break it into small steps.
3. Identify required tools, files, APIs, or data.
4. Complete the first working version.
5. Test the result.
6. Fix errors and improve.
7. Prepare final output or deployment.
"""

    add_event(
        event_type="tool_result",
        team="Tool Team",
        agent="Tool_Agent",
        tool="create_task_plan",
        output_data=result,
    )

    return result


def summarize_chat() -> str:
    """
    Summarize the current chat history.
    """
    stats["total_tool_calls"] += 1

    add_event(
        event_type="tool_call",
        team="Tool Team",
        agent="Tool_Agent",
        tool="summarize_chat",
        input_data="summarize current chat",
    )

    if not chat_history:
        result = "No chat history available yet."

        add_event(
            event_type="tool_result",
            team="Tool Team",
            agent="Tool_Agent",
            tool="summarize_chat",
            output_data=result,
        )

        return result

    last_messages = chat_history[-10:]

    summary_lines = []

    for msg in last_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        summary_lines.append(f"{role}: {content[:120]}")

    result = "Recent chat summary:\n" + "\n".join(summary_lines)

    add_event(
        event_type="tool_result",
        team="Tool Team",
        agent="Tool_Agent",
        tool="summarize_chat",
        output_data=result,
    )

    return result


def get_weather(city: str) -> str:
    """
    Demo weather tool.
    Gives a fake weather response for demonstration.
    """
    stats["total_tool_calls"] += 1

    add_event(
        event_type="tool_call",
        team="Tool Team",
        agent="Tool_Agent",
        tool="get_weather",
        input_data=city,
    )

    result = f"The weather in {city} is sunny with a high of 25°C."

    add_event(
        event_type="tool_result",
        team="Tool Team",
        agent="Tool_Agent",
        tool="get_weather",
        output_data=result,
    )

    return result


# ============================================================
# AUTOGEN MODEL CLIENT
# ============================================================

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    add_event(
        event_type="warning",
        content="OPENAI_API_KEY is missing. Add it inside your .env file.",
    )

model_client = OpenAIChatCompletionClient(
    model=MODEL_NAME,
    api_key=api_key,
    temperature=TEMPERATURE,
)


# ============================================================
# AUTOGEN TOOLS
# ============================================================

calculator_tool = FunctionTool(
    calculator,
    description="Use this tool when the user asks for math calculations.",
)

studio_info_tool = FunctionTool(
    get_studio_info,
    description="Use this tool when the user asks about Stellar Pulse Interactive, SPI, studio, or company details.",
)

task_planner_tool = FunctionTool(
    create_task_plan,
    description="Use this tool when the user asks to plan, build, create, automate, or complete a multi-step task.",
)

chat_summary_tool = FunctionTool(
    summarize_chat,
    description="Use this tool when the user asks for a summary of the current chat.",
)

weather_tool = FunctionTool(
    get_weather,
    description="Use this tool when the user asks about weather in a city.",
)


# ============================================================
# AUTOGEN AGENTS
# ============================================================

planner_agent = AssistantAgent(
    name="Planner_Agent",
    model_client=model_client,
    system_message="""
You are Planner_Agent from the Planning Team.

Your job:
- Understand the user's task.
- Break the task into clear steps.
- Decide what kind of work is needed.
- Mention whether tools may be needed.
- Keep your answer short and structured.

End your message with:
PLANNING_DONE
""",
)

task_analyst_agent = AssistantAgent(
    name="Task_Analyst_Agent",
    model_client=model_client,
    system_message="""
You are Task_Analyst_Agent from the Planning Team.

Your job:
- Analyze the user's request.
- Identify task type: chat, coding, math, weather, planning, studio info, or summary.
- Identify missing details if any.
- Explain what the next team should do.

End your message with:
PLANNING_DONE
""",
)

tool_agent = AssistantAgent(
    name="Tool_Agent",
    model_client=model_client,
    tools=[
        calculator_tool,
        studio_info_tool,
        task_planner_tool,
        chat_summary_tool,
        weather_tool,
    ],
    system_message="""
You are Tool_Agent from the Tool Team.

Your job:
- Use tools when useful.
- If the task needs calculation, use calculator.
- If the task asks weather, use get_weather.
- If the task asks about SPI or Stellar Pulse Interactive, use get_studio_info.
- If the task asks for a plan, use create_task_plan.
- If the task asks for chat summary, use summarize_chat.
- If no tool is needed, explain that no tool is required.
- Keep output clear.

End your message with:
TOOL_DONE
""",
)

reviewer_agent = AssistantAgent(
    name="Reviewer_Agent",
    model_client=model_client,
    system_message="""
You are Reviewer_Agent from the Review Team.

Your job:
- Review the planning output and tool output.
- Check if the answer is correct and useful.
- Mention any issue if found.
- Keep your review short.

End your message with:
REVIEW_DONE
""",
)

final_response_agent = AssistantAgent(
    name="Final_Response_Agent",
    model_client=model_client,
    system_message="""
You are Final_Response_Agent from the Review Team.

Your job:
- Write the final answer for the user.
- Use the planning output and tool output.
- Do not expose unnecessary internal chain.
- Be clear, simple, and helpful.
- If tool result is available, use it.
- If the user asked for code, provide complete working code.
- Do not include the word TERMINATE unless the task is complete.

End your final answer with:
TERMINATE
""",
)


# ============================================================
# AUTOGEN TEAMS
# ============================================================

planning_termination = MaxMessageTermination(max_messages=4) | TextMentionTermination("PLANNING_DONE")
tool_termination = MaxMessageTermination(max_messages=5) | TextMentionTermination("TOOL_DONE")
review_termination = MaxMessageTermination(max_messages=5) | TextMentionTermination("TERMINATE")

planning_team = RoundRobinGroupChat(
    participants=[
        planner_agent,
        task_analyst_agent,
    ],
    termination_condition=planning_termination,
)

tool_team = RoundRobinGroupChat(
    participants=[
        tool_agent,
    ],
    termination_condition=tool_termination,
)

review_team = RoundRobinGroupChat(
    participants=[
        reviewer_agent,
        final_response_agent,
    ],
    termination_condition=review_termination,
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


# ============================================================
# HELPER FUNCTIONS FOR TEAM RUNS
# ============================================================

def extract_text_from_result(result: Any) -> str:
    if not hasattr(result, "messages") or not result.messages:
        return ""

    final_message = result.messages[-1]
    content = getattr(final_message, "content", str(final_message))

    return str(content)


def clean_final_reply(text: str) -> str:
    return (
        text
        .replace("TERMINATE", "")
        .replace("PLANNING_DONE", "")
        .replace("TOOL_DONE", "")
        .replace("REVIEW_DONE", "")
        .strip()
    )


def capture_result_messages(
    result: Any,
    team_id: str,
    team_name: str,
    team_task: str,
    started_at: float,
) -> Dict[str, Any]:
    messages_data = []

    total_prompt_tokens = 0
    total_completion_tokens = 0

    if hasattr(result, "messages"):
        for msg in result.messages:
            msg_type = type(msg).__name__
            source = getattr(msg, "source", "unknown")
            content = getattr(msg, "content", "")

            prompt_tokens = 0
            completion_tokens = 0

            models_usage = getattr(msg, "models_usage", None)

            if models_usage:
                prompt_tokens = getattr(models_usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(models_usage, "completion_tokens", 0) or 0

                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens

            safe_content = str(content)

            if "ToolCallRequestEvent" in msg_type:
                category = "tool_call_request"
            elif "ToolCallExecutionEvent" in msg_type:
                category = "tool_execution_result"
            elif "TextMessage" in msg_type:
                category = "agent_message"
            else:
                category = "internal_message"

            item = {
                "type": msg_type,
                "source": source,
                "category": category,
                "content": safe_content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

            messages_data.append(item)

            add_event(
                event_type=msg_type,
                team=team_name,
                agent=source,
                content=safe_content,
            )

    duration = round(time.time() - started_at, 2)

    team_run = {
        "team_id": team_id,
        "team_name": team_name,
        "task": team_task,
        "status": "completed",
        "duration_seconds": duration,
        "messages_count": len(messages_data),
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "messages": messages_data,
        "time": now_time(),
    }

    team_runs.append(team_run)

    if len(team_runs) > 40:
        del team_runs[:20]

    return team_run


async def run_team(
    team_id: str,
    team_name: str,
    team: Any,
    task: str,
    work_description: str,
) -> Dict[str, Any]:
    update_team_status(team_id, "working", work_description)

    add_event(
        event_type="team_started",
        team=team_name,
        content=work_description,
        input_data=task,
    )

    started_at = time.time()

    result = await team.run(task=task)

    team_run = capture_result_messages(
        result=result,
        team_id=team_id,
        team_name=team_name,
        team_task=task,
        started_at=started_at,
    )

    update_team_status(team_id, "completed", work_description)

    add_event(
        event_type="team_completed",
        team=team_name,
        content=f"{team_name} completed its work.",
        output_data=extract_text_from_result(result),
    )

    return {
        "result": result,
        "run": team_run,
        "output": extract_text_from_result(result),
    }


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "online",
        "app": "SPI Multi-Team Agentic AI",
        "model": MODEL_NAME,
        "time": now_time(),
    }


@app.get("/debug-path")
def debug_path():
    return {
        "base_dir": str(BASE_DIR),
        "index_file": str(BASE_DIR / "index.html"),
        "style_file": str(BASE_DIR / "style.css"),
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    start_time = time.time()

    user_message = request.message.strip()

    if not user_message:
        return JSONResponse(
            {
                "reply": "Please type a message.",
                "overview": get_overview_data(),
            }
        )

    reset_team_statuses()

    stats["total_requests"] += 1
    stats["estimated_total_input_chars"] += len(user_message)

    stats["last_prompt_tokens"] = 0
    stats["last_completion_tokens"] = 0
    stats["last_total_tokens"] = 0
    stats["last_inner_messages"] = 0
    stats["last_active_teams"] = []
    stats["last_team_flow"] = []

    chat_history.append(
        {
            "role": "user",
            "content": user_message,
            "time": now_time(),
        }
    )

    add_event(
        event_type="user_message",
        content=user_message,
    )

    try:
        # ========================================================
        # TEAM 1: PLANNING TEAM
        # ========================================================

        planning_task = f"""
User request:
{user_message}

Create a short plan and identify what kind of work is needed.
"""

        planning_output_data = await run_team(
            team_id="planning_team",
            team_name="Planning Team",
            team=planning_team,
            task=planning_task,
            work_description="Understanding the user request and creating a plan.",
        )

        planning_output = planning_output_data["output"]

        stats["last_active_teams"].append("Planning Team")
        stats["last_team_flow"].append(
            {
                "step": 1,
                "team": "Planning Team",
                "work": "Understood the user request and created a plan.",
            }
        )

        # ========================================================
        # TEAM 2: TOOL TEAM
        # ========================================================

        tool_task = f"""
User request:
{user_message}

Planning Team output:
{planning_output}

Use tools only if needed.
If no tool is needed, say no tool is required.
"""

        tool_output_data = await run_team(
            team_id="tool_team",
            team_name="Tool Team",
            team=tool_team,
            task=tool_task,
            work_description="Checking whether tools are needed and using tools if useful.",
        )

        tool_output = tool_output_data["output"]

        stats["last_active_teams"].append("Tool Team")
        stats["last_team_flow"].append(
            {
                "step": 2,
                "team": "Tool Team",
                "work": "Used tools or confirmed no tool was required.",
            }
        )

        # ========================================================
        # TEAM 3: REVIEW TEAM
        # ========================================================

        review_task = f"""
User request:
{user_message}

Planning Team output:
{planning_output}

Tool Team output:
{tool_output}

Create the final answer for the user.
"""

        review_output_data = await run_team(
            team_id="review_team",
            team_name="Review Team",
            team=review_team,
            task=review_task,
            work_description="Reviewing team outputs and preparing the final answer.",
        )

        final_output = review_output_data["output"]
        reply = clean_final_reply(final_output)

        stats["last_active_teams"].append("Review Team")
        stats["last_team_flow"].append(
            {
                "step": 3,
                "team": "Review Team",
                "work": "Reviewed outputs and created the final user response.",
            }
        )

        # ========================================================
        # COLLECT FINAL STATS
        # ========================================================

        recent_runs = team_runs[-3:]

        total_prompt_tokens = sum(run.get("prompt_tokens", 0) for run in recent_runs)
        total_completion_tokens = sum(run.get("completion_tokens", 0) for run in recent_runs)
        total_inner_messages = sum(run.get("messages_count", 0) for run in recent_runs)

        duration = round(time.time() - start_time, 2)

        stats["total_team_runs"] += 3
        stats["last_prompt_tokens"] = total_prompt_tokens
        stats["last_completion_tokens"] = total_completion_tokens
        stats["last_total_tokens"] = total_prompt_tokens + total_completion_tokens
        stats["last_inner_messages"] = total_inner_messages
        stats["last_response_time_seconds"] = duration

        stats["estimated_total_output_chars"] += len(reply)
        stats["estimated_total_tokens"] = estimate_tokens()

        chat_history.append(
            {
                "role": "assistant",
                "content": reply,
                "time": now_time(),
            }
        )

        add_event(
            event_type="assistant_reply",
            content=reply,
        )

        return JSONResponse(
            {
                "reply": reply,
                "overview": get_overview_data(),
                "run_summary": {
                    "number_of_teams": 3,
                    "active_teams": stats["last_active_teams"],
                    "team_flow": stats["last_team_flow"],
                    "number_of_inner_messages": total_inner_messages,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "duration_seconds": duration,
                },
            }
        )

    except Exception as e:
        error_message = f"Backend error: {str(e)}"

        add_event(
            event_type="error",
            content=error_message,
        )

        return JSONResponse(
            {
                "reply": error_message,
                "overview": get_overview_data(),
            }
        )


@app.get("/overview")
def overview():
    return JSONResponse(get_overview_data())


@app.post("/reset")
def reset_chat():
    chat_history.clear()
    backend_events.clear()
    team_runs.clear()
    reset_team_statuses()

    stats["total_requests"] = 0
    stats["total_tool_calls"] = 0
    stats["total_team_runs"] = 0
    stats["last_response_time_seconds"] = 0

    stats["estimated_total_input_chars"] = 0
    stats["estimated_total_output_chars"] = 0
    stats["estimated_total_tokens"] = 0

    stats["last_prompt_tokens"] = 0
    stats["last_completion_tokens"] = 0
    stats["last_total_tokens"] = 0
    stats["last_inner_messages"] = 0

    stats["last_active_teams"] = []
    stats["last_team_flow"] = []

    add_event(
        event_type="system",
        content="Chat, backend overview, and team state reset.",
    )

    return {
        "status": "reset_done",
        "overview": get_overview_data(),
    }


def get_overview_data():
    return {
        "stats": stats,
        "teams_overview": teams_overview,
        "team_runs": team_runs[-12:],
        "chat_history": chat_history[-50:],
        "backend_events": backend_events[-140:],
    }


@app.on_event("shutdown")
async def shutdown_event():
    await model_client.close()