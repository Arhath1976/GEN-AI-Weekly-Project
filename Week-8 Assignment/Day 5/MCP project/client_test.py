import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def print_result(result):
    """
    Prints MCP tool result in a clean format.
    """
    if result.content:
        for item in result.content:
            if hasattr(item, "text"):
                print(item.text)
            else:
                print(item)
    else:
        print("No result returned.")


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()

            print("\nMCP Client Connected Successfully!")

            tools = await session.list_tools()

            print("\nAvailable Tools:")
            for tool in tools.tools:
                print("-", tool.name)

            print("\nTesting add_numbers tool:")
            add_result = await session.call_tool(
                "add_numbers",
                arguments={
                    "a": 10,
                    "b": 20
                }
            )
            print_result(add_result)

            print("\nTesting subtract_numbers tool:")
            subtract_result = await session.call_tool(
                "subtract_numbers",
                arguments={
                    "a": 50,
                    "b": 15
                }
            )
            print_result(subtract_result)

            print("\nTesting multiply_numbers tool:")
            multiply_result = await session.call_tool(
                "multiply_numbers",
                arguments={
                    "a": 7,
                    "b": 6
                }
            )
            print_result(multiply_result)

            print("\nTesting get_student_details tool:")
            student_result = await session.call_tool(
                "get_student_details",
                arguments={
                    "name": "Haresh"
                }
            )
            print_result(student_result)

            print("\nTesting create_project_plan tool:")
            plan_result = await session.call_tool(
                "create_project_plan",
                arguments={
                    "project_name": "AI Portfolio Website"
                }
            )
            print_result(plan_result)

            print("\nTesting generate_study_schedule tool:")
            schedule_result = await session.call_tool(
                "generate_study_schedule",
                arguments={
                    "subject": "Python",
                    "days": 3
                }
            )
            print_result(schedule_result)


if __name__ == "__main__":
    asyncio.run(main())