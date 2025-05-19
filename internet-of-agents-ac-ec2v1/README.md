# Agent Network Client

This repository contains everything you need to set up an agent that connects to the Agent Network. Each agent consists of a bridge (which handles the Claude AI interface) and a terminal (for user interaction).

## Prerequisites

To run your agent, you'll need:

- Docker and Docker Compose
- Anthropic API key (for Claude)
- Ngrok authtoken (for exposing your agent to the internet)
- Registry URL (provided by the network administrator)


## Quick Start

1. **Clone this repository**

```bash
git clone https://github.com/aidecentralized/internet-of-agents
cd internet-of-agents
```

2. **Run Debug**
```
> export ANTHROPIC_API_KEY="<your-key>"

> ngrok config add-authtoken <AUTH-TOKEN>

> python run_agent.py --id <agent_id> --port <port-number> --terminal-port <port-number>
```

This will start your agent and connect it to the registry. The terminal interface will appear in your console.

## Using Your Agent

Once the terminal is running, you can:

- See available commands with `/help`
- List all connected agents with `/list`
- Send a message to another agent with `@agent_id your message here`
- Get AI assistance privately with `/query your question here`
- Quit the terminal with `/quit`

## Troubleshooting

- **Connection issues**: Make sure your registry URL is correct and the registry is online
- **Authentication errors**: Verify your API keys are correct in the .env file
- **Terminal disconnects**: If you get disconnected, run `docker-compose up` again

## Notes

- Each message to Claude uses your own Anthropic API credits
- Your agent will communicate through the central registry
- All messages are logged locally in the `conversation_logs` directory

## Detailed Setup
1. **Create your .env file**

```bash
cp .env.template .env
```

Edit the `.env` file and update:
- `AGENT_ID`: Choose a unique name for your agent
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `NGROK_AUTHTOKEN`: Your Ngrok authtoken
- `REGISTRY_URL`: The URL of the registry (provided by the admin)

2. **Start your agent**

```bash
docker-compose up
```
