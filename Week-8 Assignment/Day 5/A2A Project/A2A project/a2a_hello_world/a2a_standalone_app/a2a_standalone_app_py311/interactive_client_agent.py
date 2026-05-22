import requests
import json


SERVER_URL = "http://127.0.0.1:8000/message"


def send_message(message):
    data = {
        "sender_agent": "InteractiveClientAgent",
        "receiver_agent": "ServerAgent",
        "message": message
    }

    try:
        response = requests.post(SERVER_URL, json=data)

        if response.status_code == 200:
            return response.json()

        return {
            "status": "error",
            "message": response.text
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Server Agent is not running. Start it using: python server_agent.py"
        }


def main():
    print("\nA2A Interactive Client Agent Started")
    print("Python Version Required: 3.11.0")
    print("------------------------------------")
    print("Type a message to send to ServerAgent.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_message = input("\nClientAgent: ").strip()

        if user_message.lower() in ["exit", "quit", "stop"]:
            print("ClientAgent stopped.")
            break

        result = send_message(user_message)

        print("\nServerAgent:")
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
