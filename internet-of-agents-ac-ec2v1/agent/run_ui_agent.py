# run_agent_ui.py - with Flask API wrapper
import os
import subprocess
import time
import requests
import sys
import signal
import argparse
import threading
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from python_a2a import A2AClient, Message, TextContent, MessageRole
from queue import Queue
from threading import Event

# Global variables
bridge_process = None
registry_url = None
agent_id = None
agent_port = None
app = Flask(__name__)

#CORS(app) # This enables cross-site requests
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    return response

# Message queues for SSE (Server-Sent Events)
# This allows us to push messages to the UI when they arrive
client_queues = {}

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    global bridge_process
    
    print("Cleaning up processes...")
    if bridge_process:
        bridge_process.terminate()
    
    sys.exit(0)

def get_registry_url():
    """Get the registry URL from file or use default"""
    global registry_url
    
    if registry_url:
        return registry_url
        
    try:
        if os.path.exists("registry_url.txt"):
            with open("registry_url.txt", "r") as f:
                url = f.read().strip()
                print(f"Using registry URL from file: {url}")
                return url
    except Exception as e:
        print(f"Error reading registry URL: {e}")
    
    # Default if file doesn't exist
    print("Registry URL file not found. Using default: https://localhost:6900")
    return "https://chat.nanda-registry.com:6900"

def register_agent(agent_id, public_url):
    """Register the agent with the registry"""
    reg_url = get_registry_url()
    try:
        print(f"Registering agent {agent_id} at {public_url}")
        response = requests.post(
            f"{reg_url}/register", 
            json={"agent_id": agent_id, "agent_url": public_url}
        )
        if response.status_code == 200:
            print(f"Agent {agent_id} registered successfully")
            return True
        else:
            print(f"Failed to register agent: {response.text}")
            return False
    except Exception as e:
        print(f"Error registering agent: {e}")
        return False

def lookup_agent(agent_id):
    """Look up an agent's URL in the registry"""
    reg_url = get_registry_url()
    try:
        print(f"Looking up agent {agent_id} in registry...")
        response = requests.get(f"{reg_url}/lookup/{agent_id}")
        if response.status_code == 200:
            agent_url = response.json().get("agent_url")
            print(f"Found agent {agent_id} at URL: {agent_url}")
            return agent_url
        print(f"Agent {agent_id} not found in registry")
        return None
    except Exception as e:
        print(f"Error looking up agent {agent_id}: {e}")
        return None

def add_message_to_queue(client_id, message):
    """Add a message to a client's queue for SSE streaming"""
    if client_id in client_queues:
        client_queues[client_id]['queue'].put(message)
        client_queues[client_id]['event'].set()

# Message handling endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "agent_id": agent_id})

@app.route('/api/send', methods=['POST', 'OPTIONS'])
def send_message():
    """Send a message to the agent bridge and return the response"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        # Add required CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        
        for key, value in headers.items():
            response.headers[key] = value
            
        return response

    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message in request"}), 400
        
        message_text = data['message']
        conversation_id = data.get('conversation_id')
        client_id = data.get('client_id', 'ui_client')
        
        # Create metadata for the message
        metadata = {
            'source': 'ui_client',
            'client_id': client_id
        }
        
        # Create an A2A client to talk to the agent bridge
        bridge_url = f"https://chat.nanda-registry:{agent_port}/a2a"
        client = A2AClient(bridge_url, timeout=60)
        
        # Send the message to the bridge WITHOUT preprocessing
        # Let the bridge handle "@" commands and "/query" commands
        response = client.send_message(
            Message(
                role=MessageRole.USER,
                content=TextContent(text=message_text),
                conversation_id=conversation_id,
                metadata=metadata
            )
        )
        
        # Extract the response from the agent
        if hasattr(response.content, 'text'):
            # Return the response with conversation ID
            return jsonify({
                "response": response.content.text,
                "conversation_id": response.conversation_id,
                "agent_id": agent_id
            })
        else:
            return jsonify({"error": "Received non-text response"}), 500
            
    except Exception as e:
        print(f"Error in /api/send: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agents/list', methods=['GET'])
def list_agents():
    """List all registered clients"""
    reg_url = get_registry_url()
    try:
        response = requests.get(f"{reg_url}/list")
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": f"Failed to get agent list: {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/receive_message', methods=['POST'])
def receive_message():
    """Receive a message from the agent bridge and display it"""
    try:
        data = request.json
        message = data.get('message', '')
        from_agent = data.get('from_agent', '')
        conversation_id = data.get('conversation_id', '')
        timestamp = data.get('timestamp', '')
        
        print("\n--- New message received ---")
        print(f"From: {from_agent}")
        print(f"Message: {message}")
        print(f"Conversation ID: {conversation_id}")
        print(f"Timestamp: {timestamp}")
        print("----------------------------\n")
        
        # Create a JavaScript snippet that the client can use to display this
        with open("latest_message.json", "w") as f:
            json.dump({
                "message": message,
                "from_agent": from_agent,
                "conversation_id": conversation_id,
                "timestamp": timestamp
            }, f)
        
        return jsonify({"status": "received"})
    except Exception as e:
        print(f"Error processing received message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/render', methods=['GET'])
def render_on_ui():
    try:
        if not os.path.exists("latest_message.json"):
            return jsonify({})
        else:
            latest_message = json.load(open("latest_message.json"))
            os.remove("latest_message.json")
            return jsonify(latest_message)
    except Exception as e:
        print(f"no latest message founds")
        return jsonify({"error": str(e)}), 500


@app.route('/api/messages/stream', methods=['GET'])
def stream_messages():
    """SSE endpoint for streaming messages to UI clients"""
    client_id = request.args.get('client_id')
    if not client_id or client_id not in client_queues:
        return jsonify({"error": "Client not registered"}), 400
    
    def generate():
        client_data = client_queues[client_id]
        queue = client_data['queue']
        event = client_data['event']
        
        # Send any queued messages
        while True:
            # Wait for new messages
            event.wait()
            
            # Get all queued messages
            while not queue.empty():
                message = queue.get()
                yield f"data: {json.dumps(message)}\n\n"
            
            # Reset event
            event.clear()
    
    response = Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache', 
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',  # Use * for development or specific origin for production
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )
    return response

def main():
    global bridge_process, registry_url, agent_id, agent_port
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    parser = argparse.ArgumentParser(description="Run an agent with Flask API wrapper")
    parser.add_argument("--id", required=True, help="Agent ID")
    parser.add_argument("--port", type=int, default=6000, help="Agent bridge port (default: 6000)")
    parser.add_argument("--api-port", type=int, default=5000, help="Flask API port (default: 5000)")
    parser.add_argument("--registry", help="Registry URL")
    parser.add_argument("--public-url", help="Public URL for the API")
    
    args = parser.parse_args()
    
    # Set global variables
    agent_id = args.id
    agent_port = args.port
    api_port = args.api_port
    registry_url = args.registry
    
    # Determine public URL for registration
    public_url = args.public_url
    if not public_url:
        # If no public URL is provided, use localhost or find public IP
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        
        public_url = f"https://{ip}:{api_port}"
    
    # Set environment variables for the agent bridge
    os.environ["AGENT_ID"] = agent_id
    os.environ["PORT"] = str(agent_port)
    os.environ["PUBLIC_URL"] = public_url
    os.environ["REGISTRY_URL"] = get_registry_url()
    os.environ["UI_MODE"] = "true"
    os.environ["UI_CLIENT_URL"] = f"https://localhost:{api_port}/api/receive_message"
    
    # Start the agent bridge
    print(f"Starting agent bridge for {agent_id} on port {agent_port}...")
    bridge_process = subprocess.Popen(["python3", "agent_bridge.py"])
    
    # Give the bridge a moment to start
    time.sleep(2)
    
    # Register the agent (with API URL)
    register_agent(agent_id, public_url)
    
    print("\n" + "="*50)
    print(f"Agent {agent_id} is running")
    print(f"Agent Bridge URL: https://localhost:{agent_port}/a2a")
    print(f"Client API URL: https://localhost:{api_port}")
    print("="*50)
    print("\nAPI Endpoints:")
    print(f"  GET  localhost:{api_port}/api/health - Health check")
    print(f"  POST localhost:{api_port}/api/send - Send a message to the client")
    print(f"  GET  localhost:{api_port}/api/agents - List all registered agents")
    print(f" POST: localhost:{api_port}/api/receive - Receive a message from agent")
    # print(f"  POST {public_url}/api/register - Register a UI client")
    # print(f"  GET  {public_url}/api/messages/stream - Stream messages to UI")
    print("\nPress Ctrl+C to stop all processes.")
    
    # Start the Flask API server
    app.run(host='0.0.0.0', port=api_port, threaded=True)

if __name__ == "__main__":
    main()
