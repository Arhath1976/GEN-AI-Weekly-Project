import requests
import json


SERVER_URL = "http://127.0.0.1:8000/message"


def send_message_to_agent():
    message_data = {
        "sender_agent": "ClientAgent",
        "receiver_agent": "ServerAgent",
        "message": "Hello from Client Agent using Python 3.11.0!"
    }

    print("\nClient Agent Sending Message...")
    print("--------------------------------")
    print(json.dumps(message_data, indent=4))

    try:
        response = requests.post(SERVER_URL, json=message_data)

        print("\nServer Agent Response")
        print("---------------------")

        if response.status_code == 200:
            print(json.dumps(response.json(), indent=4))
        else:
            print("Error:", response.status_code)
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\nConnection Error:")
        print("Server Agent is not running.")
        print("First run this command:")
        print("python server_agent.py")


if __name__ == "__main__":
    send_message_to_agent()
