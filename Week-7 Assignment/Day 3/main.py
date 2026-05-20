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
    title="SPI Agentic AI",
    description="Local AutoGen-powered agentic AI web app with tools and backend overview.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve CSS and static files from current folder
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")


# ============================================================
# MEMORY / BACKEND STATE
# ============================================================

chat_history: List[Dict[str, Any]] = []
backend_events: List[Dict[str, Any]] = []

stats: Dict[str, Any] = {
    "app_name": "SPI Agentic AI",
    "status": "online",
    "model": MODEL_NAME,
    "temperature": TEMPERATURE,
    "max_tokens": MAX_TOKENS,

    "total_requests": 0,
    "total_tool_calls": 0,

    "last_response_time_seconds": 0,

    "estimated_total_input_chars": 0,
    "estimated_total_output_chars": 0,
    "estimated_total_tokens": 0,

    "last_prompt_tokens": 0,
    "last_completion_tokens": 0,
    "last_total_tokens": 0,
    "last_inner_messages": 0,

    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}


def now_time() -> str:
    return time.strftime("%H:%M:%S")


def add_event(
    event_type: str,
    content: str = "",
    tool: str = "",
    input_data: str = "",
    output_data: str = "",
):
    backend_events.append(
        {
            "type": event_type,
            "tool": tool,
            "input": input_data,
            "output": output_data,
            "content": content,
            "time": now_time(),
        }
    )

    # Keep memory small
    if len(backend_events) > 150:
        del backend_events[:70]


def estimate_tokens() -> int:
    total_chars = (
        stats["estimated_total_input_chars"]
        + stats["estimated_total_output_chars"]
    )

    # Rough estimate: 1 token is around 4 characters
    return total_chars // 4


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
        tool="calculator",
        input_data=expression,
    )

    try:
        allowed_chars = "0123456789+-*/(). "

        if not all(char in allowed_chars for char in expression):
            result = "Invalid expression. Only numbers and + - * / ( ) are allowed."

            add_event(
                event_type="tool_result",
                tool="calculator",
                output_data=result,
            )

            return result

        answer = eval(expression)

        result = f"The answer is {answer}"

        add_event(
            event_type="tool_result",
            tool="calculator",
            output_data=result,
        )

        return result

    except Exception as e:
        error = f"Calculator error: {str(e)}"

        add_event(
            event_type="tool_error",
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
        tool="get_studio_info",
        input_data="studio info requested",
    )

    result = (
        "The studio name is Stellar Pulse Interactive. "
        "It focuses on games, web apps, AI tools, automation, and creative software projects."
    )

    add_event(
        event_type="tool_result",
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
        tool="summarize_chat",
        input_data="summarize current chat",
    )

    if not chat_history:
        result = "No chat history available yet."

        add_event(
            event_type="tool_result",
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
        tool="get_weather",
        input_data=city,
    )

    result = f"The weather in {city} is sunny with a high of 25°C."

    add_event(
        event_type="tool_result",
        tool="get_weather",
        output_data=result,
    )

    return result


# ============================================================
# AUTOGEN SETUP
# ============================================================

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    add_event(
        event_type="warning",
        content="OPENAI_API_KEY is missing. Add it inside your .env file.",
    )

# Safe config. If your AutoGen version rejects temperature,
# remove temperature=TEMPERATURE.
model_client = OpenAIChatCompletionClient(
    model=MODEL_NAME,
    api_key=api_key,
    temperature=TEMPERATURE,
)

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

assistant = AssistantAgent(
    name="my_assistant",
    model_client=model_client,
    tools=[
        calculator_tool,
        studio_info_tool,
        task_planner_tool,
        chat_summary_tool,
        weather_tool,
    ],
    system_message="""
You are SPI Agent, a premium local agentic AI assistant for Stellar Pulse Interactive.

Your main behavior:
- Act like an agentic AI, not just a chatbot.
- Understand the user's goal.
- Decide whether a tool is needed.
- Use tools when they help.
- Break complex tasks into clear steps.
- Give practical, beginner-friendly answers.
- Be direct, useful, and clear.

Tool rules:
- Use calculator for math.
- Use get_weather when the user asks weather for any city.
- Use studio info tool for Stellar Pulse Interactive or SPI questions.
- Use task planner tool for building, planning, automation, coding, or multi-step tasks.
- Use chat summary tool when the user asks to summarize the conversation.
- Never pretend a tool was used if it was not.
- Never say an action happened unless a tool confirms it.

Response style:
- Keep replies clean and easy to understand.
- For coding help, give complete working code when asked.
- If something is missing, ask only the necessary question.
""",
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


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
        "app": "SPI Agentic AI",
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

    stats["total_requests"] += 1
    stats["estimated_total_input_chars"] += len(user_message)

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
        result = await assistant.run(task=user_message)

        duration = round(time.time() - start_time, 2)

        final_message = result.messages[-1]
        reply = getattr(final_message, "content", str(final_message))

        stats["estimated_total_output_chars"] += len(reply)
        stats["last_response_time_seconds"] = duration
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

        # ============================================================
        # AUTOGEN INTERNAL DETAILS CAPTURE
        # ============================================================

        autogen_messages = []

        total_prompt_tokens = 0
        total_completion_tokens = 0

        for msg in result.messages:
            msg_type = type(msg).__name__
            source = getattr(msg, "source", "unknown")
            content = getattr(msg, "content", "")

            prompt_tokens = 0
            completion_tokens = 0

            # Try to capture token usage if available
            models_usage = getattr(msg, "models_usage", None)

            if models_usage:
                prompt_tokens = getattr(models_usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(models_usage, "completion_tokens", 0) or 0

                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens

            safe_content = str(content)

            autogen_item = {
                "type": msg_type,
                "source": source,
                "content": safe_content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

            if "ToolCallRequestEvent" in msg_type:
                autogen_item["category"] = "tool_call_request"

                add_event(
                    event_type="ToolCallRequestEvent",
                    content=safe_content,
                )

            elif "ToolCallExecutionEvent" in msg_type:
                autogen_item["category"] = "tool_execution_result"

                add_event(
                    event_type="ToolCallExecutionEvent",
                    content=safe_content,
                )

            elif "TextMessage" in msg_type:
                autogen_item["category"] = "assistant_message"

                add_event(
                    event_type="TextMessage",
                    content=safe_content,
                )

            else:
                autogen_item["category"] = "internal_message"

                add_event(
                    event_type=msg_type,
                    content=safe_content,
                )

            autogen_messages.append(autogen_item)

        stats["last_prompt_tokens"] = total_prompt_tokens
        stats["last_completion_tokens"] = total_completion_tokens
        stats["last_total_tokens"] = total_prompt_tokens + total_completion_tokens
        stats["last_inner_messages"] = len(result.messages)

        return JSONResponse(
            {
                "reply": reply,
                "autogen_messages": autogen_messages,
                "overview": get_overview_data(),
                "run_summary": {
                    "number_of_inner_messages": len(result.messages),
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

    stats["total_requests"] = 0
    stats["total_tool_calls"] = 0
    stats["last_response_time_seconds"] = 0

    stats["estimated_total_input_chars"] = 0
    stats["estimated_total_output_chars"] = 0
    stats["estimated_total_tokens"] = 0

    stats["last_prompt_tokens"] = 0
    stats["last_completion_tokens"] = 0
    stats["last_total_tokens"] = 0
    stats["last_inner_messages"] = 0

    add_event(
        event_type="system",
        content="Chat and backend overview reset.",
    )

    return {
        "status": "reset_done",
        "overview": get_overview_data(),
    }


def get_overview_data():
    return {
        "stats": stats,
        "chat_history": chat_history[-50:],
        "backend_events": backend_events[-100:],
    }


@app.on_event("shutdown")
async def shutdown_event():
    await model_client.close()