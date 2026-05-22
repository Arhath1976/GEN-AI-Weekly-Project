from datetime import datetime
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(
    title="A2A Standalone App",
    description="A2A Hello World app using Python 3.11.0 with math operations",
    version="1.1.0"
)

background_logs = []


class AgentMessage(BaseModel):
    sender_agent: str
    receiver_agent: str
    message: str


def add_log(event: str):
    background_logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "event": event
    })

    if len(background_logs) > 30:
        background_logs.pop(0)


def extract_numbers(text: str):
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    return [float(num) if "." in num else int(num) for num in numbers]


def calculate_from_message(message: str):
    text = message.lower().strip()
    numbers = extract_numbers(text)

    # Symbol-based operations: 10 + 20, 50 - 15, 6 * 7, 100 / 5
    symbol_match = re.search(r"(-?\d+(?:\.\d+)?)\s*([\+\-\*/x])\s*(-?\d+(?:\.\d+)?)", text)

    if symbol_match:
        a = float(symbol_match.group(1))
        operator = symbol_match.group(2)
        b = float(symbol_match.group(3))

        if operator == "+":
            return f"{a:g} + {b:g} = {a + b:g}"

        if operator == "-":
            return f"{a:g} - {b:g} = {a - b:g}"

        if operator in ["*", "x"]:
            return f"{a:g} × {b:g} = {a * b:g}"

        if operator == "/":
            if b == 0:
                return "Cannot divide by zero."
            return f"{a:g} ÷ {b:g} = {a / b:g}"

    # Word-based operations
    if any(word in text for word in ["add", "plus", "sum", "addition"]):
        if len(numbers) >= 2:
            result = sum(numbers)
            return f"The addition result is {result:g}."

    if any(word in text for word in ["subtract", "minus", "subtraction"]):
        if len(numbers) >= 2:
            result = numbers[0]
            for n in numbers[1:]:
                result -= n
            return f"The subtraction result is {result:g}."

    if any(word in text for word in ["multiply", "times", "product", "multiplication"]):
        if len(numbers) >= 2:
            result = 1
            for n in numbers:
                result *= n
            return f"The multiplication result is {result:g}."

    if any(word in text for word in ["divide", "division", "divided"]):
        if len(numbers) >= 2:
            result = numbers[0]
            for n in numbers[1:]:
                if n == 0:
                    return "Cannot divide by zero."
                result /= n
            return f"The division result is {result:g}."

    return None


@app.get("/", response_class=HTMLResponse)
def home():
    add_log("Web app opened.")

    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>A2A Standalone App - Python 3.11.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            min-height: 100vh;
            font-family: Segoe UI, Arial, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(0,255,204,0.25), transparent 35%),
                radial-gradient(circle at bottom right, rgba(124,92,255,0.28), transparent 35%),
                #070a12;
            color: white;
        }

        .app {
            width: min(1100px, 94%);
            margin: 0 auto;
            padding: 30px 0;
        }

        .topbar {
            background: rgba(13,18,32,0.85);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 26px;
            padding: 20px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 24px 80px rgba(0,0,0,0.35);
        }

        .brand h1 {
            font-size: 26px;
        }

        .brand p {
            color: #9aa4bf;
            margin-top: 5px;
        }

        .pill {
            background: rgba(0,255,204,0.1);
            color: #00ffcc;
            border: 1px solid rgba(0,255,204,0.25);
            padding: 10px 14px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 13px;
        }

        .grid {
            margin-top: 24px;
            display: grid;
            grid-template-columns: 0.9fr 1.1fr;
            gap: 22px;
        }

        .card {
            background: rgba(13,18,32,0.82);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 30px;
            padding: 28px;
            box-shadow: 0 24px 80px rgba(0,0,0,0.32);
        }

        .hero {
            min-height: 520px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .badge {
            width: fit-content;
            padding: 9px 13px;
            border-radius: 999px;
            color: #00ffcc;
            background: rgba(0,255,204,0.09);
            border: 1px solid rgba(0,255,204,0.22);
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 20px;
        }

        .hero h2 {
            font-size: clamp(36px, 5vw, 58px);
            line-height: 0.95;
            letter-spacing: -2px;
            margin-bottom: 18px;
        }

        .hero p {
            color: #aeb8d4;
            line-height: 1.7;
        }

        .flow {
            margin-top: 34px;
            display: grid;
            gap: 14px;
        }

        .agent {
            padding: 18px;
            border-radius: 20px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.09);
        }

        .agent small {
            color: #9aa4bf;
            display: block;
            margin-bottom: 6px;
        }

        .agent strong {
            font-size: 21px;
        }

        .server {
            background: rgba(124,92,255,0.15);
            border-color: rgba(124,92,255,0.35);
        }

        .arrow {
            color: #00ffcc;
            margin-left: 18px;
            padding-left: 18px;
            height: 45px;
            border-left: 2px dashed rgba(0,255,204,0.4);
            display: flex;
            align-items: center;
            font-weight: 800;
            font-size: 13px;
        }

        .chat-card {
            min-height: 520px;
            display: flex;
            flex-direction: column;
        }

        .chat-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 16px;
        }

        .chat-head h3 {
            font-size: 25px;
        }

        .chat-head p {
            color: #9aa4bf;
            margin-top: 5px;
        }

        #chat {
            flex: 1;
            background: rgba(0,0,0,0.28);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 22px;
            padding: 18px;
            overflow-y: auto;
            max-height: 390px;
        }

        .msg {
            max-width: 82%;
            margin-bottom: 12px;
            padding: 13px 15px;
            border-radius: 17px;
            line-height: 1.5;
        }

        .msg b {
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 5px;
            opacity: 0.75;
        }

        .bot {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
        }

        .user {
            margin-left: auto;
            background: linear-gradient(135deg, #00ffcc, #7c5cff);
            color: #071018;
            font-weight: 600;
        }

        form {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }

        input {
            flex: 1;
            padding: 15px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.07);
            color: white;
            outline: none;
            font-size: 15px;
        }

        button {
            border: none;
            padding: 14px 18px;
            border-radius: 16px;
            background: white;
            color: #070a12;
            font-weight: 900;
            cursor: pointer;
        }

        .quick {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .quick button,
        #overviewBtn {
            background: rgba(255,255,255,0.08);
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
            padding: 10px 12px;
            border-radius: 999px;
        }

        #overviewBtn {
            background: linear-gradient(135deg, #00ffcc, #7c5cff);
            color: #071018;
            border: none;
        }

        .panel {
            position: fixed;
            top: 0;
            right: -460px;
            width: min(460px, 92vw);
            height: 100vh;
            background: rgba(10,14,25,0.97);
            border-left: 1px solid rgba(255,255,255,0.1);
            transition: 0.25s;
            z-index: 10;
            padding: 24px;
            overflow-y: auto;
        }

        .panel.open {
            right: 0;
        }

        .panel h2 {
            margin-bottom: 5px;
        }

        .panel p {
            color: #9aa4bf;
            margin-bottom: 18px;
        }

        .panel-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .panel-card h3 {
            margin-bottom: 10px;
        }

        .panel-card li {
            margin-left: 20px;
            line-height: 1.8;
            color: #c7d0ea;
        }

        #logs {
            background: rgba(0,0,0,0.25);
            padding: 12px;
            border-radius: 14px;
            color: #c7d0ea;
            font-size: 13px;
            white-space: pre-wrap;
        }

        .close {
            float: right;
            background: rgba(255,255,255,0.08);
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 8px 12px;
        }

        @media(max-width: 850px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .topbar {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }
        }
    </style>
</head>
<body>

    <div class="app">
        <header class="topbar">
            <div class="brand">
                <h1>A2A Standalone App</h1>
                <p>Agent-to-Agent Communication Demo • Python 3.11.0 • Math Operations Enabled</p>
            </div>

            <div>
                <span class="pill">ServerAgent Online</span>
                <button id="overviewBtn" onclick="openPanel()">Overview</button>
            </div>
        </header>

        <main class="grid">
            <section class="card hero">
                <div class="badge">PYTHON 3.11.0 A2A DEMO</div>
                <h2>Two agents talking through an API.</h2>
                <p>
                    The browser acts as ClientAgent. FastAPI acts as ServerAgent.
                    Your message is sent to the backend and the ServerAgent replies.
                </p>

                <div class="flow">
                    <div class="agent">
                        <small>Sender</small>
                        <strong>ClientAgent</strong>
                    </div>

                    <div class="arrow">POST /message</div>

                    <div class="agent server">
                        <small>Receiver</small>
                        <strong>ServerAgent</strong>
                    </div>
                </div>
            </section>

            <section class="card chat-card">
                <div class="chat-head">
                    <div>
                        <h3>Agent Console</h3>
                        <p>Try: add 10 and 20, 50 - 15, multiply 6 and 7.</p>
                    </div>
                    <span class="pill">LIVE</span>
                </div>

                <div id="chat">
                    <div class="msg bot">
                        <b>ServerAgent</b>
                        Hello! I can answer basic messages and do add, subtract, multiply, and divide.
                    </div>
                </div>

                <form onsubmit="sendMessage(event)">
                    <input id="msgInput" placeholder="Type: add 10 and 20..." required>
                    <button type="submit">Send</button>
                </form>

                <div class="quick">
                    <button onclick="quickSend('add 10 and 20')">Add</button>
                    <button onclick="quickSend('subtract 50 and 15')">Subtract</button>
                    <button onclick="quickSend('multiply 6 and 7')">Multiply</button>
                    <button onclick="quickSend('divide 100 by 5')">Divide</button>
                    <button onclick="quickSend('What is A2A?')">What is A2A?</button>
                    <button onclick="quickSend('Status')">Status</button>
                </div>
            </section>
        </main>
    </div>

    <aside class="panel" id="panel">
        <button class="close" onclick="closePanel()">×</button>
        <h2>System Overview</h2>
        <p>What is running in the background</p>

        <div class="panel-card">
            <h3>Running Components</h3>
            <ul>
                <li>Python 3.11.0 virtual environment</li>
                <li>FastAPI backend server</li>
                <li>ServerAgent /message endpoint</li>
                <li>Math operation parser</li>
                <li>Browser ClientAgent UI</li>
                <li>JavaScript fetch communication</li>
            </ul>
        </div>

        <div class="panel-card">
            <h3>Supported Operations</h3>
            <ul>
                <li>add 10 and 20</li>
                <li>10 + 20</li>
                <li>subtract 50 and 15</li>
                <li>50 - 15</li>
                <li>multiply 6 and 7</li>
                <li>6 * 7</li>
                <li>divide 100 by 5</li>
                <li>100 / 5</li>
            </ul>
        </div>

        <div class="panel-card">
            <h3>Live Logs</h3>
            <button onclick="loadOverview()">Refresh Logs</button>
            <div id="logs">Click refresh logs.</div>
        </div>
    </aside>

    <script>
        const chat = document.getElementById("chat");
        const input = document.getElementById("msgInput");

        function addMessage(sender, text, type) {
            const div = document.createElement("div");
            div.className = "msg " + type;
            div.innerHTML = "<b>" + sender + "</b>" + text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function sendToServer(text) {
            addMessage("ClientAgent", text, "user");

            try {
                const res = await fetch("/message", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        sender_agent: "ClientAgent",
                        receiver_agent: "ServerAgent",
                        message: text
                    })
                });

                const data = await res.json();
                addMessage("ServerAgent", data.reply, "bot");

            } catch (err) {
                addMessage("System", "Connection failed. Server may not be running.", "bot");
            }
        }

        function sendMessage(event) {
            event.preventDefault();
            const text = input.value.trim();

            if (!text) {
                return;
            }

            input.value = "";
            sendToServer(text);
        }

        function quickSend(text) {
            sendToServer(text);
        }

        function openPanel() {
            document.getElementById("panel").classList.add("open");
            loadOverview();
        }

        function closePanel() {
            document.getElementById("panel").classList.remove("open");
        }

        async function loadOverview() {
            const logs = document.getElementById("logs");
            logs.textContent = "Loading...";

            try {
                const res = await fetch("/overview");
                const data = await res.json();

                if (!data.recent_logs || data.recent_logs.length === 0) {
                    logs.textContent = "No logs yet.";
                    return;
                }

                logs.textContent = data.recent_logs
                    .slice()
                    .reverse()
                    .map(log => "[" + log.time + "] " + log.event)
                    .join("\\n");

            } catch (err) {
                logs.textContent = "Could not load logs.";
            }
        }
    </script>

</body>
</html>
    """


@app.get("/health")
def health():
    add_log("Health endpoint checked.")

    return {
        "status": "running",
        "project": "A2A Standalone App",
        "python_version": "3.11.0",
        "server_agent": "active",
        "math_operations": "enabled"
    }


@app.get("/overview")
def overview():
    add_log("Overview requested.")

    return {
        "project": "A2A Standalone App",
        "python_version": "3.11.0",
        "status": "running",
        "active_agents": [
            "ClientAgent",
            "ServerAgent"
        ],
        "supported_operations": [
            "add 10 and 20",
            "10 + 20",
            "subtract 50 and 15",
            "50 - 15",
            "multiply 6 and 7",
            "6 * 7",
            "divide 100 by 5",
            "100 / 5"
        ],
        "background_process": [
            "FastAPI server is running.",
            "Browser acts as ClientAgent.",
            "JavaScript sends message to /message.",
            "ServerAgent checks if message is math operation.",
            "If math operation is detected, result is calculated.",
            "If normal text is detected, normal response is returned.",
            "Browser displays response."
        ],
        "recent_logs": background_logs
    }


@app.post("/message")
def receive_message(data: AgentMessage):
    add_log(f"Message received from {data.sender_agent}: {data.message}")

    math_result = calculate_from_message(data.message)

    if math_result is not None:
        reply_text = math_result
    else:
        user_message = data.message.lower().strip()

        reply_text = f"Hello {data.sender_agent}, I am {data.receiver_agent}. Your message was received successfully!"

        if "hello" in user_message or "hi" in user_message:
            reply_text = f"Hello {data.sender_agent}! ServerAgent is online and ready."
        elif "a2a" in user_message:
            reply_text = "A2A means Agent-to-Agent communication. One agent sends a message to another agent through an API."
        elif "status" in user_message:
            reply_text = "ServerAgent status: active. FastAPI is running. /message endpoint is working. Math operations are enabled."
        elif "python" in user_message:
            reply_text = "This project is built for Python 3.11.0."
        elif "help" in user_message:
            reply_text = "Try: add 10 and 20, 10 + 20, subtract 50 and 15, 50 - 15, multiply 6 and 7, 6 * 7, divide 100 by 5, or 100 / 5."
        elif "how are you" in user_message:
            reply_text = "ServerAgent is running perfectly."

    add_log(f"Reply sent to {data.sender_agent}: {reply_text}")

    return {
        "from_agent": data.receiver_agent,
        "to_agent": data.sender_agent,
        "received_message": data.message,
        "reply": reply_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": "3.11.0",
        "status": "success"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server_agent:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )