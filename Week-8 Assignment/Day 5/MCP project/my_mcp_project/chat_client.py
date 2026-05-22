import asyncio
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def extract_text(result):
    """
    Extract clean text from MCP result.
    """
    if not result.content:
        return "No result returned."

    output = []

    for item in result.content:
        if hasattr(item, "text"):
            output.append(item.text)
        else:
            output.append(str(item))

    return "\n".join(output)


def extract_numbers(text):
    """
    Extract numbers from user text.
    """
    numbers = re.findall(r"-?\d+", text)
    return [int(num) for num in numbers]


def extract_days(text):
    """
    Extract number of days from text.
    """
    numbers = extract_numbers(text)
    if numbers:
        return numbers[0]
    return 3


def extract_subject(text):
    """
    Extract subject for study schedule.
    """
    lower_text = text.lower()

    if "python" in lower_text:
        return "Python"
    if "ai" in lower_text:
        return "AI"
    if "mcp" in lower_text:
        return "MCP"
    if "math" in lower_text:
        return "Math"
    if "cyber" in lower_text:
        return "Cyber Security"

    return "General Subject"


def extract_project_name(text):
    """
    Extract project name from user text.
    """
    lower_text = text.lower()

    trigger_phrases = [
        "project plan for",
        "plan for",
        "create project plan for",
        "make project plan for",
        "build",
        "create"
    ]

    for phrase in trigger_phrases:
        if phrase in lower_text:
            project = text.lower().split(phrase, 1)[1].strip()
            if project:
                return project.title()

    return "New Project"


async def call_and_print(session, tool_name, arguments):
    """
    Call MCP tool and print clean result.
    """
    result = await session.call_tool(tool_name, arguments=arguments)
    print("\nAssistant:")
    print(extract_text(result))


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()

            print("\nMCP Chat Client Started Successfully!")
            print("Type your question below.")
            print("Type 'exit' or 'quit' to stop.")
            print("\nExamples:")
            print("- what is mcp")
            print("- add 10 and 20")
            print("- subtract 50 and 15")
            print("- multiply 7 and 6")
            print("- student details of Haresh")
            print("- create project plan for AI Portfolio Website")
            print("- study schedule for Python 5 days")

            while True:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["exit", "quit", "stop"]:
                    print("\nAssistant: Goodbye!")
                    break

                lower_input = user_input.lower()

                # Addition
                if "add" in lower_input or "sum" in lower_input or "plus" in lower_input:
                    numbers = extract_numbers(user_input)

                    if len(numbers) >= 2:
                        await call_and_print(
                            session,
                            "add_numbers",
                            {
                                "a": numbers[0],
                                "b": numbers[1]
                            }
                        )
                    else:
                        print("\nAssistant: Please provide two numbers to add.")

                # Subtraction
                elif "subtract" in lower_input or "minus" in lower_input:
                    numbers = extract_numbers(user_input)

                    if len(numbers) >= 2:
                        await call_and_print(
                            session,
                            "subtract_numbers",
                            {
                                "a": numbers[0],
                                "b": numbers[1]
                            }
                        )
                    else:
                        print("\nAssistant: Please provide two numbers to subtract.")

                # Multiplication
                elif "multiply" in lower_input or "product" in lower_input or "times" in lower_input:
                    numbers = extract_numbers(user_input)

                    if len(numbers) >= 2:
                        await call_and_print(
                            session,
                            "multiply_numbers",
                            {
                                "a": numbers[0],
                                "b": numbers[1]
                            }
                        )
                    else:
                        print("\nAssistant: Please provide two numbers to multiply.")

                # Student details
                elif "student" in lower_input or "details" in lower_input:
                    words = user_input.split()

                    name = "Haresh"
                    for word in words:
                        if word.lower() not in ["student", "details", "of", "get", "show", "for"]:
                            name = word
                            break

                    await call_and_print(
                        session,
                        "get_student_details",
                        {
                            "name": name
                        }
                    )

                # Project plan
                elif "project plan" in lower_input or "plan for" in lower_input:
                    project_name = extract_project_name(user_input)

                    await call_and_print(
                        session,
                        "create_project_plan",
                        {
                            "project_name": project_name
                        }
                    )

                # Study schedule
                elif "study schedule" in lower_input or "schedule" in lower_input:
                    subject = extract_subject(user_input)
                    days = extract_days(user_input)

                    await call_and_print(
                        session,
                        "generate_study_schedule",
                        {
                            "subject": subject,
                            "days": days
                        }
                    )

                # Normal question answering
                else:
                    await call_and_print(
                        session,
                        "answer_user_question",
                        {
                            "question": user_input
                        }
                    )


if __name__ == "__main__":
    asyncio.run(main())