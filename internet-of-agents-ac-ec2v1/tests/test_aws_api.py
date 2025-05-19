import requests

# List all agents
response = requests.get("http://localhost:6006/api/agents/list")
agents = response.json()
print("Available agents:", agents)

# Send a message to prad
response = requests.post(
    "http://localhost:6006/api/send",
    json={
        "message": "@prad Weather today is great!!!",
        "client_id": "adambot",
        "conversation_id": "test_conversation_123"
    }
)
result = response.json()
print("Message result:", result)

response = requests.post(
    "http://localhost:6006/api/receive_message",  # Replace with your actual port
    json={"message": "Test message", "from_agent": "test", "conversation_id": "test123"}
)
print("Status:", response.status_code)
print("Response:", response.text)

