import requests
import time

# List all agents
response = requests.get("https://chat.nanda-registry.com:6900/sender/agent4")
breakpoint()
agents = response.json()
print("Sender name:", agents)


exit()

# Receive a message

# Send a message to prad
response = requests.post(
    "https://chat.nanda-registry.com:6001/api/send",
    json={
        "message": "@agent1 India is great. Weather today is great!!!",
        "client_id": "1929294949",
        "userProfile": {"name": "mihirsheth"},
        "conversation_id": "test_conversation_123"
    }
)
result = response.json()
print("Message result:", result)

time.sleep(10)

response = requests.get(
    "https://chat.nanda-registry.com:6001/api/render",
)
print(response.json())

