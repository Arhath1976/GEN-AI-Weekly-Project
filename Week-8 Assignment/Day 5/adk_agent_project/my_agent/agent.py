from google.adk.agents import Agent


def get_current_time(city: str) -> dict:
    """
    Returns a simple fake current time for a given city.
    This is a demo tool for the ADK agent.

    Args:
        city: The city name.

    Returns:
        A dictionary containing the city and time information.
    """

    city_lower = city.lower().strip()

    demo_times = {
        "chennai": "11:30 AM",
        "mumbai": "11:30 AM",
        "delhi": "11:30 AM",
        "bangalore": "11:30 AM",
        "new york": "2:00 AM",
        "london": "7:00 AM",
        "tokyo": "3:00 PM",
    }

    time = demo_times.get(city_lower, "Time data not available for this city")

    return {
        "city": city,
        "current_time": time,
        "status": "success",
    }


def calculate_simple_math(expression: str) -> dict:
    """
    Safely calculates simple math expressions.

    Args:
        expression: A simple math expression like '10 + 20' or '5 * 6'.

    Returns:
        A dictionary containing the result.
    """

    allowed_chars = "0123456789+-*/(). "

    if not all(char in allowed_chars for char in expression):
        return {
            "expression": expression,
            "result": None,
            "status": "error",
            "message": "Only simple math expressions are allowed.",
        }

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result,
            "status": "success",
        }
    except Exception as error:
        return {
            "expression": expression,
            "result": None,
            "status": "error",
            "message": str(error),
        }


def create_task_plan(goal: str) -> dict:
    """
    Creates a simple step-by-step task plan for a user goal.

    Args:
        goal: The user's goal.

    Returns:
        A dictionary containing a task plan.
    """

    plan = [
        f"Understand the goal: {goal}",
        "Break the goal into smaller steps.",
        "Identify required tools, files, or information.",
        "Complete each step one by one.",
        "Review the final result and improve if needed.",
    ]

    return {
        "goal": goal,
        "plan": plan,
        "status": "success",
    }


root_agent = Agent(
    name="smart_assistant_agent",
    model="gemini-2.0-flash",
    description="A helpful agentic AI assistant that can answer questions, use tools, calculate, and create plans.",
    instruction="""
You are a smart agentic AI assistant.

Your job:
1. Understand the user's request.
2. Decide if a tool is needed.
3. Use tools when useful.
4. Give clear, simple, and helpful answers.
5. If the user asks for planning, create a step-by-step plan.
6. If the user asks for simple math, use the math tool.
7. If the user asks for current time in a city, use the time tool.

Always explain the final answer clearly.
""",
    tools=[
        get_current_time,
        calculate_simple_math,
        create_task_plan,
    ],
)
