#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Define the list of ports and API ports
BRIDGE_PORTS=(6000 6002 6004 6006 6008 6010 6012)
API_PORTS=(6001 6003 6005 6007 6009 6011 6013)

# Get the server IP address (assumes a public IP)
SERVER_IP=$(curl -s http://checkip.amazonaws.com)

# If the above command fails, try another method
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(curl -s ifconfig.me)
fi

# If both methods fail, use the provided IP
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="18.212.184.117"
    echo "Could not determine IP automatically, using default: $SERVER_IP"
else
    echo "Detected server IP: $SERVER_IP"
fi

# Start each agent
for i in "${!BRIDGE_PORTS[@]}"; do
    AGENT_ID="agent$((i+1))"
    BRIDGE_PORT=${BRIDGE_PORTS[$i]}
    API_PORT=${API_PORTS[$i]}
    PUBLIC_URL="http://$SERVER_IP:$BRIDGE_PORT"
    
    echo "Starting $AGENT_ID on bridge port $BRIDGE_PORT and API port $API_PORT"
    echo "Public URL: $PUBLIC_URL"
    
    nohup python -u run_ui_agent.py --id "$AGENT_ID" --port "$BRIDGE_PORT" --api-port "$API_PORT" --public-url "$PUBLIC_URL" > "logs/${AGENT_ID}_logs.txt" 2>&1 &
    
    # Store the process ID for later reference
    echo "$!" > "logs/${AGENT_ID}.pid"
    
    echo "$AGENT_ID started with PID $!"
    
    # Wait a few seconds between agent starts to avoid race conditions
    sleep 2
done

echo "All agents started successfully!"
echo "Use the following command to check if agents are running:"
echo "ps aux | grep run_ui_agent"
echo ""
echo "To stop all agents:"
echo "for pid in logs/*.pid; do kill \$(cat \$pid); done"