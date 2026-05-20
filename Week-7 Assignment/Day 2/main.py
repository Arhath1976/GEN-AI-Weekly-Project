import os
import asyncio
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()

async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    assistant = AssistantAgent(
        name="SPI_Assistant",
        model_client=model_client,
        system_message="""
You are SPI Assistant, a helpful AI assistant for Stellar Pulse Interactive.
You explain things clearly, help with coding, automation, and game development.
Keep answers simple, useful, and beginner-friendly.
"""
    )

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Assistant: Goodbye!")
            break

        result = await assistant.run(task=user_input)
        print("\nAssistant:", result.messages[-1].content)

    await model_client.close()

asyncio.run(main())