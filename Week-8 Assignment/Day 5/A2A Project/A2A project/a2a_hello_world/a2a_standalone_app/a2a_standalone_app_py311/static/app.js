const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const chatWindow = document.getElementById("chatWindow");

const overviewBtn = document.getElementById("overviewBtn");
const sidePanel = document.getElementById("sidePanel");
const closePanel = document.getElementById("closePanel");
const overlay = document.getElementById("overlay");
const refreshOverview = document.getElementById("refreshOverview");
const logsBox = document.getElementById("logsBox");

const quickButtons = document.querySelectorAll(".quick-actions button");

function addMessage(sender, text, type) {
    const message = document.createElement("div");
    message.className = message ;

    const label = document.createElement("span");
    label.className = "message-label";
    label.textContent = sender;

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    message.appendChild(label);
    message.appendChild(paragraph);

    chatWindow.appendChild(message);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendAgentMessage(text) {
    addMessage("ClientAgent", text, "user");

    const typingId = "typing-" + Date.now();

    const typing = document.createElement("div");
    typing.className = "message bot";
    typing.id = typingId;
    typing.innerHTML = 
        <span class="message-label">ServerAgent</span>
        <p>Processing A2A message...</p>
    ;

    chatWindow.appendChild(typing);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch("/message", {
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

        const data = await response.json();

        const typingElement = document.getElementById(typingId);

        if (typingElement) {
            typingElement.remove();
        }

        if (data.status === "success") {
            addMessage("ServerAgent", data.reply, "bot");
        } else {
            addMessage("ServerAgent", "Something went wrong while processing the message.", "bot");
        }

    } catch (error) {
        const typingElement = document.getElementById(typingId);

        if (typingElement) {
            typingElement.remove();
        }

        addMessage("System", "Connection error. Make sure the FastAPI server is running.", "bot");
    }
}

messageForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const text = messageInput.value.trim();

    if (!text) {
        return;
    }

    sendAgentMessage(text);
    messageInput.value = "";
});

quickButtons.forEach(button => {
    button.addEventListener("click", function () {
        const message = button.getAttribute("data-message");
        sendAgentMessage(message);
    });
});

function openPanel() {
    sidePanel.classList.add("open");
    overlay.classList.add("show");
    loadOverview();
}

function closeSidePanel() {
    sidePanel.classList.remove("open");
    overlay.classList.remove("show");
}

overviewBtn.addEventListener("click", openPanel);
closePanel.addEventListener("click", closeSidePanel);
overlay.addEventListener("click", closeSidePanel);
refreshOverview.addEventListener("click", loadOverview);

async function loadOverview() {
    logsBox.innerHTML = "<p>Loading background process...</p>";

    try {
        const response = await fetch("/overview");
        const data = await response.json();

        if (!data.recent_logs || data.recent_logs.length === 0) {
            logsBox.innerHTML = "<p>No logs yet. Send a message to generate background activity.</p>";
            return;
        }

        logsBox.innerHTML = "";

        data.recent_logs.slice().reverse().forEach(log => {
            const line = document.createElement("div");
            line.className = "log-line";
            line.textContent = [] ;
            logsBox.appendChild(line);
        });

    } catch (error) {
        logsBox.innerHTML = "<p>Unable to load overview. Server may not be running.</p>";
    }
}
