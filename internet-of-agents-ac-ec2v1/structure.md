# Repository File Structure

Here's the complete file structure for your GitHub repository:

```
agent-network-client/
├── agent_bridge.py        # The bridge that connects to Claude and other agents
├── agent_terminal.py      # The terminal interface for user interaction
├── docker-compose.yml     # Configuration for Docker container
├── Dockerfile             # Instructions to build the Docker image
├── .env.template          # Template for environment variables
├── README.md              # Instructions for users
├── requirements.txt       # Python dependencies
├── run_agent.py           # Script to run the agent (modified to hide logs)
└── start-agent.sh         # Startup script for Docker container
```

## What Each Friend Needs

1. A copy of this repository
2. Docker and Docker Compose installed
3. Their own Anthropic API key
4. Their own Ngrok authtoken
5. The URL of your registry server (which you'll provide)

## Your Registry Setup

On your AWS/Akamai server, you'll need to:

1. Set up the registry server using the registry.py and run_registry.py files
2. Expose the registry on a public IP/domain
3. Share this public URL with your friends

## Workflow for Your Friends

1. Clone the repository
2. Create .env file with their API keys and your registry URL
3. Run `docker-compose up`
4. Interact with their agent and connect to others through your registry
