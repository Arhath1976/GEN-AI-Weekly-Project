from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Own MCP Server")


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers and return the result.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    """
    return a + b


@mcp.tool()
def subtract_numbers(a: int, b: int) -> int:
    """
    Subtract two numbers and return the result.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Difference of a and b.
    """
    return a - b


@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """
    Multiply two numbers and return the result.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Product of a and b.
    """
    return a * b


@mcp.tool()
def get_student_details(name: str) -> dict:
    """
    Return sample student details based on name.

    Args:
        name: Student name.

    Returns:
        Student details.
    """

    students = {
        "haresh": {
            "name": "Haresh",
            "course": "Computer Science",
            "skills": ["Python", "AI", "Game Development", "Unreal Engine"],
            "status": "Active Student"
        },
        "john": {
            "name": "John",
            "course": "AI and Data Science",
            "skills": ["Machine Learning", "Python"],
            "status": "Active Student"
        },
        "sara": {
            "name": "Sara",
            "course": "Cyber Security",
            "skills": ["Networking", "Linux", "Ethical Hacking"],
            "status": "Active Student"
        }
    }

    key = name.lower().strip()

    if key in students:
        return students[key]

    return {
        "name": name,
        "course": "Unknown",
        "skills": [],
        "status": "Student not found"
    }


@mcp.tool()
def create_project_plan(project_name: str) -> dict:
    """
    Create a simple step-by-step project plan.

    Args:
        project_name: Name of the project.

    Returns:
        Project plan.
    """

    return {
        "project_name": project_name,
        "steps": [
            "Understand the project requirements",
            "Choose the technology stack",
            "Create the folder structure",
            "Build the main features",
            "Test the project",
            "Fix bugs and errors",
            "Prepare documentation",
            "Submit or deploy the project"
        ],
        "status": "Project plan created successfully"
    }


@mcp.tool()
def generate_study_schedule(subject: str, days: int) -> dict:
    """
    Generate a simple study schedule.

    Args:
        subject: Subject name.
        days: Number of days.

    Returns:
        Study schedule.
    """

    schedule = []

    for day in range(1, days + 1):
        schedule.append({
            "day": day,
            "task": f"Study {subject} topic {day} and revise previous topics"
        })

    return {
        "subject": subject,
        "days": days,
        "schedule": schedule,
        "status": "Study schedule created"
    }


@mcp.tool()
def answer_user_question(question: str) -> dict:
    """
    Answer simple user questions using built-in knowledge.

    Args:
        question: User question.

    Returns:
        Answer to the question.
    """

    q = question.lower().strip()

    knowledge_base = {
        "what is mcp": "MCP stands for Model Context Protocol. It allows AI assistants to connect with external tools, files, APIs, databases, and services in a standard way.",
        "what is model context protocol": "Model Context Protocol is a standard protocol that helps AI applications communicate with tools and external data sources.",
        "what is python": "Python is a high-level programming language used for web development, AI, automation, data science, scripting, and software development.",
        "what is ai": "AI stands for Artificial Intelligence. It is the ability of machines to perform tasks that normally require human intelligence, such as reasoning, learning, and decision-making.",
        "what is agentic ai": "Agentic AI is an AI system that can understand a goal, plan steps, use tools, and complete tasks with some level of autonomy.",
        "what is an mcp server": "An MCP server is a program that exposes tools, resources, or prompts so an AI client can use them.",
        "what is an mcp client": "An MCP client is an application that connects to an MCP server and calls its tools or reads its resources.",
        "what is a tool": "In MCP, a tool is a function exposed by the server. The client or AI assistant can call that function to perform an action.",
        "what is vscode": "VS Code is a popular code editor developed by Microsoft. It is used for writing, running, and debugging code.",
        "what is virtual environment": "A virtual environment is an isolated Python environment used to install packages separately for each project.",
        "what is pip": "pip is the package installer for Python. It is used to install external Python libraries.",
        "what is api": "API stands for Application Programming Interface. It allows different software systems to communicate with each other.",
    }

    if q in knowledge_base:
        return {
            "question": question,
            "answer": knowledge_base[q],
            "status": "answered"
        }

    if "mcp" in q:
        answer = "MCP means Model Context Protocol. It helps AI systems connect to external tools and data sources."
    elif "python" in q:
        answer = "Python is a beginner-friendly programming language widely used in AI, automation, web apps, and data science."
    elif "agentic" in q or "agent" in q:
        answer = "Agentic AI can plan, decide, use tools, and complete tasks based on a user's goal."
    elif "server" in q:
        answer = "A server is a program that provides services, data, or tools to another program called a client."
    elif "client" in q:
        answer = "A client is a program that connects to a server and requests data, tools, or services."
    elif "tool" in q:
        answer = "A tool is a function that an AI system can call to perform a specific task."
    elif "api" in q:
        answer = "An API allows two software systems to communicate with each other."
    elif "venv" in q or "virtual environment" in q:
        answer = "A virtual environment keeps Python packages isolated for a specific project."
    else:
        answer = (
            "I can answer basic questions about MCP, Python, AI, tools, servers, clients, APIs, and virtual environments. "
            "For this question, I do not have enough built-in knowledge yet."
        )

    return {
        "question": question,
        "answer": answer,
        "status": "answered"
    }


@mcp.resource("info://server")
def server_info() -> str:
    """
    Return information about this MCP server.
    """
    return """
CUSTOM MCP SERVER INFORMATION

This is a custom MCP server created using Python.

Available Tools:
1. add_numbers
2. subtract_numbers
3. multiply_numbers
4. get_student_details
5. create_project_plan
6. generate_study_schedule
7. answer_user_question

Purpose:
This server demonstrates how AI assistants can connect to external tools using Model Context Protocol.
"""


if __name__ == "__main__":
    mcp.run()