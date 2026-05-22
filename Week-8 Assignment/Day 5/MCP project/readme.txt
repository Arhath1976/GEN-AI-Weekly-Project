MCP PROJECT:
Custom MCP Server with ADK Agent Integration

PROJECT DESCRIPTION:

This project is a custom Model Context Protocol server built using Python 3.11. The main purpose of this project is to demonstrate how an AI system can connect with external tools through MCP and use those tools through an ADK agent.

MCP stands for Model Context Protocol. It is a protocol that allows AI assistants and agentic AI systems to communicate with external tools, services, APIs, files, and data sources in a standard way. In this project, a custom MCP server was created to expose multiple tools that can be used by an AI client or an ADK agent.

The MCP server includes several custom tools such as addition, subtraction, multiplication, student detail retrieval, project plan generation, study schedule generation, and basic question answering. Each tool is written as a Python function and registered inside the MCP server using the FastMCP framework.

This project was also integrated with Google ADK, which stands for Agent Development Kit. ADK is used to create an agentic AI assistant that can understand user requests, decide which MCP tool should be used, call the correct tool, and return a final answer to the user. This makes the project more powerful because the user does not need to manually call tools. Instead, the ADK agent acts as an intelligent layer between the user and the MCP server.

The workflow of the project is:

User gives a request
↓
ADK agent understands the request
↓
ADK agent connects to the MCP server
↓
MCP server executes the required tool
↓
Tool result is returned to the ADK agent
↓
ADK agent gives the final answer to the user

The project was developed in Visual Studio Code using Python 3.11. A virtual environment was created to manage project dependencies. The required packages include mcp, google-adk, and python-dotenv. The Gemini API key is stored securely inside a .env file and is used by the ADK agent to process user requests.

The MCP server is created in server.py. This file contains all the MCP tools and resources. The client_test.py file is used to test whether the MCP server tools are working correctly. The chat_client.py file provides an interactive terminal-based client that allows the user to ask questions and call MCP tools. The adk_mcp_agent folder contains the ADK agent files, including agent.py, __init__.py, and .env.

This project demonstrates important concepts of agentic AI, including tool calling, client-server communication, MCP integration, and ADK-based AI agent development. It shows how AI assistants can go beyond simple text generation by using external tools to perform real actions and return useful results.

TECHNOLOGIES USED:

1. Python 3.11
2. Model Context Protocol
3. FastMCP
4. Google ADK
5. Gemini API
6. Visual Studio Code
7. Python Virtual Environment
8. dotenv for environment variables

MAIN FEATURES:

1. Custom MCP server creation
2. Multiple MCP tools
3. MCP client testing
4. Interactive question answering client
5. ADK agent integration
6. Gemini-powered agentic AI
7. Tool calling through MCP
8. Clean project structure
9. Secure API key handling using .env
10. Python 3.11 virtual environment setup

TOOLS CREATED IN MCP SERVER:

1. add_numbers
   This tool adds two numbers and returns the result.

2. subtract_numbers
   This tool subtracts one number from another and returns the result.

3. multiply_numbers
   This tool multiplies two numbers and returns the result.

4. get_student_details
   This tool returns sample student details based on the given student name.

5. create_project_plan
   This tool creates a simple step-by-step project plan for a given project name.

6. generate_study_schedule
   This tool generates a study schedule for a selected subject and number of days.

7. answer_user_question
   This tool answers basic questions related to MCP, Python, AI, APIs, tools, servers, clients, and virtual environments.

PROJECT STRUCTURE:

my_mcp_project/
│
├── .venv/
├── server.py
├── client_test.py
├── chat_client.py
├── requirements.txt
├── guide.txt
│
└── adk_mcp_agent/
    ├── __init__.py
    ├── agent.py
    └── .env

HOW THE PROJECT WAS MADE:

First, a Python 3.11 virtual environment was created to keep all dependencies isolated. Then the required packages were installed using pip. After that, a custom MCP server was created using FastMCP. Python functions were written for different tasks and registered as MCP tools.

Next, a client_test.py file was created to connect to the MCP server and test all available tools. After confirming that the MCP tools worked correctly, an interactive chat_client.py file was added so users could type questions and receive responses through the MCP tools.

Finally, Google ADK was added to the project. An ADK agent was created inside the adk_mcp_agent folder. This agent connects to the MCP server using MCPToolset and uses the available MCP tools to answer user requests. The Gemini API key was added in the .env file so the ADK agent can process natural language input.

PURPOSE OF THE PROJECT:

The purpose of this project is to show how an AI assistant can use external tools through MCP and how ADK can be used to build an intelligent agent around those tools. This project proves that AI systems can be connected to custom Python tools and can perform useful tasks based on user instructions.

CONCLUSION:

This project successfully implements a custom MCP server and integrates it with an ADK agent. The MCP server provides external tools, and the ADK agent uses those tools intelligently based on user input. This project is a practical example of agentic AI, tool calling, and Model Context Protocol integration using Python.
