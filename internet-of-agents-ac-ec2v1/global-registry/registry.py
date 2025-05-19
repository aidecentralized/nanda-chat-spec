# registry.py
from flask import Flask, request, jsonify
import json
import os
import random
from datetime import datetime
from flask_cors import CORS
# MongoDB integration
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

app = Flask(__name__)
CORS(app)

# File to store the registry
DEFAULT_PORT = 6900
AGENT_REGISTRY_FILE = "agent_registry.json"
BRIDGE_URL = "http://34.204.70.176"

CLIENT_PUBLIC_URL = "https://chat.nanda-registry.com"

# Initialize the registry
if os.path.exists(AGENT_REGISTRY_FILE):
    with open(AGENT_REGISTRY_FILE, 'r') as f:
        try:
            registry = json.load(f)
        except:
            registry = {}
else:
    registry = {}
    with open(AGENT_REGISTRY_FILE, 'w') as f:
        json.dump(registry, f)

# new code for managing client mappings
CLIENT_REGISTRY_FILE = "client_registry.json"

# Initialize the client registry
if os.path.exists(CLIENT_REGISTRY_FILE):
    with open(CLIENT_REGISTRY_FILE, 'r') as f:
        try:
            client_registry = json.load(f)
        except:
            client_registry = {}
else:
    client_registry = {}
    with open(CLIENT_REGISTRY_FILE, 'w') as f:
        json.dump(client_registry, f)

# --- MongoDB integration ---------------------------------------------------
# We now persist registry and client data to a MongoDB Atlas cluster instead
# of local JSON files. If the connection fails we fall back to JSON files.

# ------------------ MongoDB Configuration ------------------
# The service will attempt to persist data to MongoDB if the
# `MONGODB_URI` / `MONGO_URI` environment variable is provided (or falls back
# to the default Atlas URI below).  `MONGODB_DB` lets you override the DB
# name (defaults to `iot_agents_db`).

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or (
    "mongodb+srv://mihirsheth2911:wx1mxUn2788jLdnl@cluster0.fvevtjx.mongodb.net/?retryWrites=true&w=majority"
)

MONGO_DBNAME = os.getenv("MONGODB_DB", "iot_agents_db")

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command("ping")  # Verify connection

    mongo_db = mongo_client[MONGO_DBNAME]
    agent_registry_col = mongo_db["agent_registry"]
    client_registry_col = mongo_db["client_registry"]
    messages_col = mongo_db["messages"]  # For agent logs

    USE_MONGO = True
    print("Connected to MongoDB successfully – using MongoDB for persistence.")
except Exception as e:
    print(
        f"[registry] WARNING: Could not connect to MongoDB ({e}). Falling back to JSON files."
    )
    USE_MONGO = False

# ---------------- Initial Data Load ------------------------
if USE_MONGO:
    # Reconstruct `registry` dict from MongoDB
    registry = {"agent_status": {}}
    try:
        for doc in agent_registry_col.find():
            agent_id = doc.get("agent_id")
            if not agent_id:
                continue
            registry[agent_id] = doc.get("agent_url")
            registry["agent_status"][agent_id] = {
                "alive": doc.get("alive", False),
                "assigned_to": doc.get("assigned_to"),
                "last_update": doc.get("last_update"),
            }
        print(f"[registry] Loaded {len(registry) - 1} agents from MongoDB")
    except Exception as e:
        print(f"[registry] Error loading agent registry from MongoDB: {e}")
        registry = {"agent_status": {}}

    # Reconstruct `client_registry` dict from MongoDB
    client_registry = {"agent_map": {}}
    try:
        for doc in client_registry_col.find():
            client_name = doc.get("client_name")
            if not client_name:
                continue
            client_registry[client_name] = doc.get("client_url")
            client_registry["agent_map"][client_name] = doc.get("agent_id")
        print(f"[registry] Loaded {len(client_registry) - 1} clients from MongoDB")
    except Exception as e:
        print(f"[registry] Error loading client registry from MongoDB: {e}")
        client_registry = {"agent_map": {}}
else:
    # JSON-file values already set earlier – nothing to do
    pass

# ---------------------------------------------------------------------------

# ---------------- Define helper functions BEFORE routes -------------------

def save_client_registry():
    """Persist the client registry to MongoDB or fallback to file."""
    if USE_MONGO:
        try:
            for client_name, client_url in client_registry.items():
                if client_name == 'agent_map':
                    continue
                agent_id = client_registry.get('agent_map', {}).get(client_name)
                client_registry_col.update_one(
                    {"client_name": client_name},
                    {"$set": {"client_url": client_url, "agent_id": agent_id}},
                    upsert=True,
                )
        except Exception as e:
            print(f"[registry] Error saving client registry to MongoDB: {e}")
    else:
        with open(CLIENT_REGISTRY_FILE, 'w') as f:
            json.dump(client_registry, f, indent=4)


def save_registry():
    """Persist the agent registry to MongoDB or fallback to file."""
    if USE_MONGO:
        try:
            for agent_id, agent_url in registry.items():
                if agent_id == 'agent_status':
                    continue
                status = registry.get('agent_status', {}).get(agent_id, {})
                agent_registry_col.update_one(
                    {"agent_id": agent_id},
                    {"$set": {
                        "agent_url": agent_url,
                        "alive": status.get('alive', False),
                        "assigned_to": status.get('assigned_to'),
                        "last_update": status.get('last_update'),
                    }},
                    upsert=True,
                )
        except Exception as e:
            print(f"[registry] Error saving agent registry to MongoDB: {e}")
    else:
        with open(AGENT_REGISTRY_FILE, 'w') as f:
            json.dump(registry, f, indent=4)

# --------------------------------------------------------------------------

@app.route('/api/allocate', methods=['POST'])
def allocate_agent():
    data = request.json
    if not data or 'client_id' not in data:
        return jsonify({"error": "Missing client_name"}), 400
    
    # Extract email from the user profile if available
    user_email = data['userProfile'].get('email')
    is_returning_user = False
    
    # Initialize email to username mapping if not exists
    if 'email_to_username' not in client_registry:
        client_registry['email_to_username'] = {}
    
    # Check if this email already exists
    if user_email and user_email in client_registry['email_to_username']:
        # Returning user - use their previous username
        existing_username = client_registry['email_to_username'][user_email]
        str_name = existing_username
        client_name = str_name.replace(" ", "").lower()
        is_returning_user = True
        print(f"Returning user with email {user_email} - using existing username: {client_name}")
    else:
        # New user - use the provided name
        str_name = data['userProfile']['name']
        client_name = str_name.replace(" ", "").lower()
        
        # Store the email to username mapping for future logins
        if user_email:
            client_registry['email_to_username'][user_email] = str_name
            print(f"New user with email {user_email} - saving username: {client_name}")
    
    # Check if this client already has an agent
    if client_name in client_registry:
        client_url = client_registry[client_name]

        return jsonify({
            "status": "allocated",
            "message": f"Client {client_name} is already allocated.. try a different name",
            "agent_url": client_url,
            "is_returning_user": is_returning_user
            })
  
    # Find an available agent from the main registry
    available_agents = []
    
    # First, find all allocated client URLs and convert to bridge URLs
    assigned_bridge_urls = set()

    existing_clients = []
    for key, value in client_registry.items():
        # Only consider string values as URLs
        if key == "agent_map" or key == "email_to_username":
            continue
        if isinstance(value, str):
            existing_clients.append(value)

    for c_url in existing_clients:
        parts = c_url.split(':')
        if len(parts) >= 3:
            try:
                port = int(parts[-1])
                bridge_port = port - 1
                bridge_url = f"{BRIDGE_URL}:" + str(bridge_port)
                #bridge_url = ':'.join(parts[:-1]) + ':' + str(bridge_port)
                assigned_bridge_urls.add(bridge_url)
            except ValueError:
                continue
    
    # Loop through all agents in the registry to find available ones
    for agent_id, agent_url in registry.items():
        if agent_id != 'agent_status' and agent_url not in assigned_bridge_urls:
            available_agents.append((agent_id, agent_url))
    
    if not available_agents:
        return jsonify({"error": "No available agents at this time"}), 503
    
    # Select a random available agent
    selected_agent_id, selected_agent_url = random.choice(available_agents)

    # Determine client URL (API port is typically bridge port + 1)
    client_url_port = int(selected_agent_url.split(":")[-1]) + 1
    client_url = f"{CLIENT_PUBLIC_URL}:{client_url_port}"
    #client_url = ':'.join(selected_agent_url.split(":")[:-1]) + ":" + str(client_url_port)
    print(f"Client URL allocated: {client_url}")
    
    # Assign the agent to this client
    client_registry[client_name] = client_url
    
    # client-name to agent-id mapping
    if 'agent_map' not in client_registry:
        client_registry['agent_map'] = {}

    client_registry['agent_map'][client_name] = selected_agent_id

    save_client_registry()

    print("Selected Agent ID: ", selected_agent_id)

    # Update agent status to show it's alive and assigned to this client
    if 'agent_status' in registry and selected_agent_id in registry['agent_status']:
        registry['agent_status'][selected_agent_id]['alive'] = True
        registry['agent_status'][selected_agent_id]['assigned_to'] = client_name
        registry['agent_status'][selected_agent_id]['last_update'] = datetime.now().isoformat()
        save_registry()
    
    # Return the assigned agent info with is_returning_user flag
    return jsonify({
        "status": "success", 
        "agent_url": client_url,
        "message": f"Agent {selected_agent_id} assigned to {client_name}",
        "is_returning_user": is_returning_user
    })

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'agent_id' not in data or 'agent_url' not in data:
        return jsonify({"error": "Missing agent_id or agent_url"}), 400
    
    agent_id = data['agent_id']
    agent_url = data['agent_url']
    
    # Store the agent URL in the registry
    registry[agent_id] = agent_url
    
    # Initialize or update the agent_status section
    if 'agent_status' not in registry:
        registry['agent_status'] = {}
    
    # Set default status values
    registry['agent_status'][agent_id] = {
        'alive': False,
        'assigned_to': None,
        'last_update': datetime.now().isoformat()
    }
    
    # Save the updated registry
    save_registry()
    
    return jsonify({"status": "success", "message": f"Agent {agent_id} registered successfully"})

@app.route('/lookup/<id>', methods=['GET'])
def lookup(id):
    """
    Lookup an agent by either agent_id or client_name
    """
    # First, try looking up by agent_id
    if id in registry and id != 'agent_status':
        # Direct lookup in agent registry
        agent_url = registry[id]
        return jsonify({
            "agent_id": id, 
            "agent_url": agent_url
        })
    
    # Next, try looking up by client_name
    if id in client_registry:
        # Get the client URL (which is for the UI, not the agent bridge)
        agent_id = client_registry["agent_map"][id]
        agent_url = registry[agent_id]

        return jsonify({
            "agent_id": agent_id,
            "agent_url": agent_url
            }) 
    
    # If not found in either registry
    return jsonify({"error": f"ID '{id}' not found"}), 404

@app.route('/sender/<agent_id>', methods=['GET'])
def resolve_sender(agent_id):
    if not agent_id in registry['agent_status']:
        return jsonify({"error": "Unassigned agent"}), 400

    try:
        sender_name = registry['agent_status'][agent_id]['assigned_to']
        print("Sender name: ", sender_name) 
        return jsonify({'sender_name': sender_name})
    except:
        return jsonify({"error": "No client alive for this agent"}), 404

@app.route('/list', methods=['GET'])
def list_agents():
    # Return the registry (excluding agent_status for cleaner output)
    result = {k: v for k, v in registry.items() if k != 'agent_status'}
    return jsonify(result)

@app.route('/status/<agent_id>', methods=['GET'])
def agent_status(agent_id):
    """Return the status of all agents"""
    if 'agent_status' in registry:
        return jsonify(registry['agent_status'][agent_id]["alive"])
    return jsonify({})

@app.route('/clients', methods=['GET'])
def list_clients():
    """Return the client registry"""
    result = {k: 'alive' for k, v in client_registry.items() if k != 'agent_map'}
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))

    app.run(
    ssl_context=(
        '/home/ec2-user/certificates/fullchain.pem',
        '/home/ec2-user/certificates/privkey.pem'
    ), 
        host='0.0.0.0', 
        port=port
    )

    #app.run(ssl_context="adhoc", host='0.0.0.0', port=port)
