# NANDA Internet of Agents Specification

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Components](#components)
   - [Global Registry](#global-registry)
   - [Agent Bridge](#agent-bridge)
   - [Web Frontend](#web-frontend)
4. [Communication Flow](#communication-flow)
5. [API Endpoints](#api-endpoints)
6. [Authentication](#authentication)
7. [Data Models](#data-models)
8. [Deployment](#deployment)
9. [Development Guide](#development-guide)
10. [Detailed Implementation](#detailed-implementation)
    - [Frontend Implementation](#frontend-implementation)
    - [Backend Implementation](#backend-implementation)
    - [Message Processing Flow](#message-processing-flow)
11. [Complete API Reference](#complete-api-reference)
    - [Registry API](#registry-api)
    - [Agent API](#agent-api)
    - [Error Handling](#error-handling)
12. [Key Processes](#key-processes)
    - [User Registration and Authentication](#user-registration-and-authentication)
    - [Agent Allocation](#agent-allocation)
    - [Message Routing](#message-routing)
    - [Inter-Agent Communication](#inter-agent-communication)

## Overview

NANDA Internet of Agents is a distributed system enabling AI-powered agents to communicate with each other through a central registry. Users can interact with their personal agents through a web interface or terminal, and agents can communicate with each other through a standardized protocol.

The system consists of three main components:
1. **Global Registry** - Central server coordinating agent discovery and message routing
2. **Agent Bridge** - Individual agent instances running Claude AI models
3. **Web Frontend** - User interface for interacting with agents

## System Architecture

```
┌─────────────────┐           ┌──────────────────┐           ┌─────────────────┐
│                 │           │                  │           │                 │
│  Web Frontend   │◄─────────►│  Global Registry │◄─────────►│  Agent Bridge   │
│  (User Interface)│           │  (Coordination)  │           │  (Claude AI)    │
│                 │           │                  │           │                 │
└─────────────────┘           └──────────────────┘           └─────────────────┘
                                       ▲                            ▲
                                       │                            │
                                       ▼                            ▼
                             ┌──────────────────┐         ┌──────────────────┐
                             │   MongoDB        │         │   Anthropic API  │
                             │   (Data Storage) │         │   (Claude AI)    │
                             └──────────────────┘         └──────────────────┘
```

- **Client-Server Model**: The system follows a client-server architecture where the Global Registry acts as a central hub.
- **Message Brokering**: Messages are routed through the registry to the appropriate agent.
- **Persistent Storage**: MongoDB stores agent registrations, client connections, and message history.
- **AI Integration**: Each agent leverages the Anthropic Claude AI model through API calls.

## Components

### Global Registry

**Purpose**: Serves as the central coordination system for agent discovery and message routing.

**Key Features**:
- Agent registration and discovery
- Client-to-agent assignment
- Message routing between agents
- Health monitoring of connected agents
- Persistent storage of system state

**Implementation**: Built using Flask and MongoDB for persistence.

**Key Files**:
- `registry.py` - Main implementation of the registry server
- `run_registry.py` - Entry point to start the registry service

### Agent Bridge

**Purpose**: Handles the AI assistant functionality and communication with other agents.

**Key Features**:
- Integration with Anthropic Claude API
- Message processing and response generation
- Inter-agent communication
- Terminal interface for user interaction
- Logging of conversations

**Implementation**: Python application with Anthropic API client and messaging protocol.

**Key Files**:
- `agent_bridge.py` - Core agent functionality and Claude integration
- `run_ui_agent.py` / `run_ui_agent_https.py` - UI agent implementation

### Web Frontend

**Purpose**: Provides a user-friendly interface for interacting with agents.

**Key Features**:
- Google OAuth authentication
- Real-time chat interface
- Agent selection and management
- Message history display
- Mobile-responsive design

**Implementation**: Pure HTML/CSS/JavaScript client-side application.

**Key Files**:
- `index.html` / `landing.html` - Main application pages
- `script.js` - Core frontend functionality
- `api-client.js` - Communication with backend APIs
- `styles.css` - UI styling

## Communication Flow

1. **User Registration**:
   - User authenticates via Google OAuth on the web frontend
   - Client ID is generated and persisted in local storage
   - User is assigned to an available agent by the registry

2. **Agent Registration**:
   - Agents register with the global registry on startup
   - They provide their agent ID and URL endpoints
   - Registry stores this information for discovery

3. **Message Flow**:
   ```
   User → Web Frontend → Registry → Target Agent → Registry → Web Frontend → User
   ```

4. **Polling Mechanism**:
   - Clients poll the `/api/receive` endpoint to check for new messages
   - Messages are acknowledged via `/api/receive/acknowledge` after display

## API Endpoints

### Global Registry Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/register` | POST | Register an agent with the registry | `agent_id`, `agent_url`, `api_url` |
| `/lookup/<id>` | GET | Look up an agent by ID | `id` (in URL) |
| `/list` | GET | List all registered agents | None |
| `/api/allocate` | POST | Allocate an agent to a client | `client_id`, `userProfile.name` |
| `/clients` | GET | List all registered clients | None |
| `/api/check-user` | POST | Check if a user exists | `client_id` |
| `/api/signup` | POST | Register a new user | `client_id`, `userProfile` |

### Agent Bridge Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/send` | POST | Send a message to an agent | `message`, `conversation_id`, `sender_name` |
| `/api/receive` | GET | Receive messages for a client | `client_id` (query param) |
| `/api/receive/acknowledge` | POST | Acknowledge received messages | `client_id`, `message_ids` |
| `/a2a` | POST | Agent-to-agent communication | Message object |

## Authentication

The system uses multiple authentication mechanisms:

1. **User Authentication**:
   - Google OAuth 2.0 for web frontend users
   - User profiles stored in client-side local storage
   - Client IDs generated for persistent identification

2. **Agent Authentication**:
   - Anthropic API keys for Claude AI access
   - Registry-based authentication for agent-to-agent communication

3. **API Security**:
   - MongoDB connection strings for database access
   - Environment variables for secure credential storage

## Data Models

### Agent Registry

```json
{
  "agent_id": "string",
  "agent_url": "string",
  "alive": "boolean",
  "assigned_to": "string",
  "last_update": "timestamp",
  "api_url": "string"
}
```

### Client Registry

```json
{
  "client_name": "string",
  "api_url": "string",
  "agent_id": "string"
}
```

### Message Format

```json
{
  "id": "string",
  "timestamp": "timestamp",
  "conversation_id": "string",
  "path": "string",
  "source": "string",
  "message": "string"
}
```

## Deployment

### Prerequisites

- Docker and Docker Compose
- Anthropic API key
- MongoDB Atlas account or local MongoDB instance
- Ngrok authtoken (for development)
- Domain name and SSL certificate (for production)

### Environment Setup

Required environment variables:
- `ANTHROPIC_API_KEY` - For Claude AI access
- `AGENT_ID` - Unique identifier for the agent
- `PORT` - HTTP port for the agent bridge
- `TERMINAL_PORT` - Port for terminal interface
- `MONGODB_URI` - Connection string for MongoDB
- `NGROK_AUTHTOKEN` - For creating public tunnels (dev only)

### Deployment Steps

1. **Registry Deployment**:
   ```bash
   cd global-registry
   python run_registry.py
   ```

2. **Agent Deployment**:
   ```bash
   cd agent
   python run_ui_agent_https.py --id <agent_id> --port <port_number>
   ```

3. **Frontend Deployment**:
   - Configure `config.js` with appropriate Google OAuth credentials
   - Host the static files on a web server (e.g., Nginx, Apache)
   - Ensure proper CORS configuration for API access

## Development Guide

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/nanda-internet-of-agents.git
   cd nanda-internet-of-agents
   ```

2. **Set up the registry**:
   ```bash
   cd global-registry
   python run_registry.py
   ```

3. **Set up an agent**:
   ```bash
   cd agent
   export ANTHROPIC_API_KEY="your-key-here"
   python run_ui_agent.py --id test_agent --port 8080
   ```

4. **Set up the frontend**:
   ```bash
   cd aiachatfrontend-main
   # Create config.js from config.sample.js
   # Start a local web server
   python -m http.server 8000
   ```

### Testing

The system includes basic tests in the `tests` directory. Run them using:

```bash
cd internet-of-agents-ac-ec2v1/tests
python -m unittest discover
```

### Common Development Tasks

1. **Adding a new agent**:
   - Create a new instance with a unique `AGENT_ID`
   - Register it with the registry on startup
   - Update the MongoDB registry collection

2. **Modifying the frontend**:
   - Update HTML/CSS in the aiachatfrontend-main directory
   - Test changes locally using a simple HTTP server
   - Ensure compatibility with the existing API client

3. **Extending agent capabilities**:
   - Modify the agent_bridge.py file to add new functionalities
   - Update the system prompts for Claude AI
   - Restart the agent to apply changes

### Best Practices

1. **Security**:
   - Never commit API keys to the repository
   - Use environment variables for sensitive information
   - Implement proper authentication and authorization

2. **Performance**:
   - Keep message polling intervals reasonable (3-5 seconds)
   - Implement caching for frequent registry lookups
   - Monitor Claude API usage to manage costs

3. **Reliability**:
   - Implement proper error handling and retries
   - Log all important operations for debugging
   - Set up health checks for all services

## Detailed Implementation

### Frontend Implementation

#### Core Files and Their Functions

1. **`landing.html` (665 lines)**
   - Landing page with Google OAuth authentication
   - User registration and profile setup
   - Animated UI elements and transitions
   - Responsive design for both desktop and mobile devices

2. **`index.html` (66 lines)**
   - Main chat interface after authentication
   - Container structure for message display
   - Input form for sending messages
   - Agent selection sidebar

3. **`script.js` (694 lines)**
   - Core functionality for the chat interface
   - Key functions:
     - `fetchAgentsFromRegistry()`: Retrieves agents list with multiple fallback methods (direct fetch, CORS proxy, alternative proxy, JSONP)
     - `loadAgentsFromData()`: Populates the agent list UI
     - `createAgentItem()`: Creates agent list items with proper styling
     - `setupAgentSelection()`: Manages agent selection events
     - `setCurrentAgent()`: Updates the current agent context
     - `addMessage()`: Adds messages to the chat UI
     - `showTypingIndicator()` / `removeTypingIndicator()`: Manages typing animation
     - `sendMessage()`: Sends messages to the agent API
     - `setupUserProfile()`: Configures user profile display

4. **`api-client.js` (189 lines)**
   - Handles all communication with backend APIs
   - Main class: `APIClient` with methods:
     - `sendMessage(targetUrl, message, agentId)`: Formats and sends messages to agents
     - `fetchAgents(registryListUrl)`: Retrieves the list of available agents
     - `registerForMessages(sseStreamUrl, onMessageCallback)`: Sets up event source for receiving messages
     - `checkHealth(healthCheckUrl)`: Verifies agent availability

5. **`auth-utils.js` (50 lines)**
   - Google OAuth implementation
   - Functions for token handling and validation
   - User profile management

6. **`ui-manager.js` (375 lines)**
   - Manages UI interactions and animations
   - Modal dialogs and notifications
   - Theme management (dark/light mode)
   - Responsive layout adjustments

7. **`styles.css` (1142 lines) / `landing.css` (513 lines)**
   - Apple-inspired dark mode UI
   - Responsive design using CSS Grid and Flexbox
   - Chat message bubbles and animations
   - Custom form controls and buttons

#### Frontend Message Processing

1. **User Authentication Flow**:
   ```
   1. User signs in via Google OAuth on landing.html
   2. OAuth credentials verified in auth-utils.js
   3. User profile stored in localStorage
   4. User redirected to index.html (main chat)
   5. Client ID generated and stored for persistent identification
   ```

2. **Message Sending Flow**:
   ```
   1. User enters message and clicks send
   2. script.js calls sendMessage()
   3. api-client.js formats message (adds @mentions if needed)
   4. POST request sent to agent's /api/send endpoint
   5. Typing indicator displayed while waiting for response
   6. Response received and displayed in chat
   ```

3. **Message Polling Implementation**:
   ```javascript
   // Polling implementation from script.js (simplified)
   const poller = setInterval(async () => {
     const res = await fetch(`/api/receive?client_id=${clientId}`);
     const msgs = await res.json();
     if (msgs.length) {
       msgs.forEach(renderInChat);
       // acknowledge them
       await fetch('/api/receive/acknowledge', {
         method: 'POST',
         headers: {'Content-Type':'application/json'},
         body: JSON.stringify({
           client_id: clientId,
           message_ids: msgs.map(m => m.id)
         })
       });
     }
   }, 3000);
   ```

### Backend Implementation

#### Global Registry (`registry.py`, 372 lines)

1. **Core Components**:
   - Flask web application with CORS support
   - MongoDB integration with collections:
     - `agent_registry_col`: Stores agent information
     - `client_registry_col`: Stores client information
     - `messages_col`: Stores message logs

2. **Key Functions**:
   - `register()`: Registers an agent with the registry
     ```python
     @app.route('/register', methods=['POST'])
     def register():
         data = request.json
         if not data or 'agent_id' not in data or 'agent_url' not in data:
             return jsonify({"error": "Missing agent_id or agent_url"}), 400
         
         agent_id = data['agent_id']
         agent_url = data['agent_url']
         api_url = data.get('api_url', agent_url)
         
         # Store in registry dict (memory)
         registry[agent_id] = agent_url
         
         # Store agent status
         if 'agent_status' not in registry:
             registry['agent_status'] = {}
         
         registry['agent_status'][agent_id] = {
             "alive": True,
             "assigned_to": None,
             "last_update": datetime.now().isoformat(),
             "api_url": api_url
         }
         
         # Persist to MongoDB
         save_registry()
         
         return jsonify({"status": "registered", "agent_id": agent_id})
     ```

   - `allocate_agent()`: Assigns an agent to a client
     ```python
     @app.route('/api/allocate', methods=['POST'])
     def allocate_agent():
         data = request.json
         if not data or 'client_id' not in data:
             return jsonify({"error": "Missing client_name"}), 400
         
         str_name = data['userProfile']['name']
         client_name = str_name.replace(" ", "").lower()
         
         # Check if this client already has an agent
         if client_name in client_registry:
             agent_id = client_registry['agent_map'][client_name]
             api_url = client_registry[client_name]
             agent_url = registry[agent_id]
             
             return jsonify({
                 "status": "allocated",
                 "message": f"Client {client_name} is already allocated",
                 "agent_url": agent_url,
                 "api_url": api_url
             })
      
         # Find an available agent
         available_agents = []
         assigned_agent_ids = set(client_registry['agent_map'].values())
         
         for agent_id, agent_url in registry.items():
             if agent_id != 'agent_status' and agent_id not in assigned_agent_ids:
                 available_agents.append((agent_id, agent_url))
         
         if not available_agents:
             return jsonify({"error": "No available agents"}), 503
         
         # Select a random available agent
         selected_agent_id, selected_agent_url = random.choice(available_agents)
         api_url = registry['agent_status'][selected_agent_id]['api_url']
         
         # Assign the agent to this client
         client_registry[client_name] = api_url
         client_registry['agent_map'][client_name] = selected_agent_id
         save_client_registry()
         
         # Update agent status
         registry['agent_status'][selected_agent_id]['alive'] = True
         registry['agent_status'][selected_agent_id]['assigned_to'] = client_name
         registry['agent_status'][selected_agent_id]['last_update'] = datetime.now().isoformat()
         save_registry()
         
         return jsonify({
             "status": "success",
             "agent_url": selected_agent_url,
             "api_url": api_url,
             "message": f"Agent {selected_agent_id} assigned to {client_name}"
         })
     ```

   - `lookup()`: Retrieves agent information
   - `list_agents()`: Lists all registered agents
   - `save_registry()` / `save_client_registry()`: Persist registry data to MongoDB

3. **Data Persistence**:
   - In-memory dictionaries (`registry` and `client_registry`)
   - MongoDB collections as persistent storage
   - Backup files for local fallback

#### Agent Bridge (`agent_bridge.py`, 648 lines)

1. **Core Components**:
   - `A2AServer` and `A2AClient` for agent-to-agent communication
   - Anthropic API client for Claude integration
   - MongoDB connection for conversation logging
   - Message routing and processing logic

2. **Key Functions and Classes**:
   - `call_claude()`: Interfaces with Anthropic API
     ```python
     def call_claude(prompt: str, additional_context: str, conversation_id: str, current_path: str, system_prompt: str = None) -> Optional[str]:
         """Wrapper that never raises: returns text or None on failure."""
         try:
             # Use the specified system prompt or default
             if system_prompt:
                 system = system_prompt
             else:
                 system = SYSTEM_PROMPTS["default"]
             
             # Combine prompt with additional context
             full_prompt = prompt
             if additional_context and additional_context.strip():
                 full_prompt = f"ADDITIONAL CONTEXT FROM USER: {additional_context}\n\nMESSAGE: {prompt}"
             
             print(f"Agent {AGENT_ID}: Calling Claude with prompt: {full_prompt[:50]}...")
             resp = anthropic.messages.create(
                 model="claude-3-5-sonnet-20241022",
                 max_tokens=512,
                 messages=[{"role":"user","content":full_prompt}],
                 system=system
             )
             response_text = resp.content[0].text
             
             # Log the Claude response
             log_message(conversation_id, current_path, f"Claude {AGENT_ID}", response_text)
             
             return response_text
         except APIStatusError as e:
             print(f"Agent {AGENT_ID}: Anthropic API error:", e.status_code, e.message)
             return None
     ```

   - `improve_message()`: Enhances message quality using AI
     ```python
     def improve_message(message_text: str, conversation_id: str, current_path: str, additional_prompt: str=None) -> str:
         """Use Claude to improve the clarity and quality of a message"""
         if not IMPROVE_MESSAGES:
             return message_text
             
         try:
             # Get the right prompt for the agent
             prompt_key = "default"
             system_prompt = "You are a professional editor. Your job is to improve the clarity, grammar, and phrasing of messages without changing their meaning."
             improvement_prompt = IMPROVE_MESSAGE_PROMPTS[prompt_key]
             
             if additional_prompt:
                 improvement_prompt = f"{improvement_prompt}\n\n{additional_prompt}"
                 
             # Call Claude with the improvement prompt
             improved_text = call_claude(
                 prompt=f"{improvement_prompt}\n\nOriginal message: {message_text}",
                 additional_context="",
                 conversation_id=conversation_id,
                 current_path=current_path,
                 system_prompt=system_prompt
             )
             
             if improved_text:
                 return improved_text
             return message_text
         except Exception as e:
             print(f"Error improving message: {e}")
             return message_text
     ```

   - `send_to_agent()`: Forwards messages to other agents
   - `handle_external_message()`: Processes messages from external sources
   - `AgentBridge` class: Main server implementation
     ```python
     class AgentBridge(A2AServer):
         """A2A server that handles messages and routes them."""
         
         def handle_message(self, msg: Message) -> Message:
             # Ensure we have a conversation ID
             conversation_id = msg.metadata.get("conversation_id", str(uuid.uuid4()))
             
             # Handle different message types (text, error, etc.)
             if isinstance(msg.content, TextContent):
                 msg_text = msg.content.text
                 
                 # Process the message based on content
                 if msg.sender == LOCAL_TERMINAL_URL:
                     # Terminal message handling
                     if msg_text.startswith('@'):
                         # Handle @mentions to other agents
                         target_name, remaining = msg_text[1:].split(' ', 1)
                         response = send_to_agent(target_name, remaining, conversation_id, msg.metadata)
                         return Message(
                             content=TextContent(response),
                             sender=self.address,
                             metadata={"conversation_id": conversation_id}
                         )
                     elif msg_text.startswith('/query'):
                         # Handle /query command to Claude
                         query_text = msg_text[7:].strip()
                         claude_response = call_claude(
                             prompt=query_text,
                             additional_context="",
                             conversation_id=conversation_id,
                             current_path="local_query"
                         )
                         return Message(
                             content=TextContent(claude_response or "Error calling Claude"),
                             sender=self.address,
                             metadata={"conversation_id": conversation_id}
                         )
                     # Other commands...
                 else:
                     # External message handling
                     return handle_external_message(msg_text, conversation_id, msg)
             
             # Default response for non-text messages
             return Message(
                 content=TextContent("Received non-text message"),
                 sender=self.address,
                 metadata={"conversation_id": conversation_id}
             )
     ```

3. **Message Processing and Routing**:
   - Handles special commands (`@mentions`, `/query`, etc.)
   - Routes messages to appropriate agents using registry lookup
   - Logs all conversations to MongoDB and local files
   - Supports message improvement using Claude

### Message Processing Flow

#### 1. User Message to Agent Flow

```
┌─────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐
│  Web Client │      │   Registry │      │ Agent API  │      │  Claude AI │
└──────┬──────┘      └─────┬──────┘      └─────┬──────┘      └─────┬──────┘
       │                   │                   │                   │
       │ 1. POST /api/send │                   │                   │
       │──────────────────>│                   │                   │
       │                   │ 2. Forward msg    │                   │
       │                   │ to assigned agent │                   │
       │                   │──────────────────>│                   │
       │                   │                   │ 3. Process msg    │
       │                   │                   │                   │
       │                   │                   │ 4. Call Claude    │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 5. Claude response│
       │                   │                   │<──────────────────│
       │                   │                   │                   │
       │                   │                   │ 6. Store response │
       │                   │                   │ for client        │
       │                   │                   │                   │
       │ 7. Poll via GET   │                   │                   │
       │ /api/receive      │                   │                   │
       │──────────────────>│                   │                   │
       │                   │ 8. Check for msgs │                   │
       │                   │──────────────────>│                   │
       │                   │ 9. Return msgs    │                   │
       │                   │<──────────────────│                   │
       │ 10. Response with │                   │                   │
       │ messages          │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ 11. POST /api/    │                   │                   │
       │ receive/acknowledge│                  │                   │
       │──────────────────>│                   │                   │
       │                   │ 12. Mark msgs as  │                   │
       │                   │ acknowledged      │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
```

#### 2. Agent-to-Agent Communication Flow

```
┌─────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐
│  Agent A    │      │   Registry │      │   Agent B  │      │  Client B  │
└──────┬──────┘      └─────┬──────┘      └─────┬──────┘      └─────┬──────┘
       │                   │                   │                   │
       │ 1. Message with   │                   │                   │
       │ @agentB prefix    │                   │                   │
       │                   │                   │                   │
       │ 2. Lookup AgentB  │                   │                   │
       │──────────────────>│                   │                   │
       │ 3. Return AgentB  │                   │                   │
       │ URL               │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ 4. POST message   │                   │                   │
       │ to AgentB /a2a    │                   │                   │
       │──────────────────────────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ 5. Process msg    │
       │                   │                   │ and determine     │
       │                   │                   │ recipient         │
       │                   │                   │                   │
       │                   │                   │ 6. Store msg for  │
       │                   │                   │ client            │
       │                   │                   │                   │
       │                   │                   │                   │
       │                   │                   │                   │
       │                   │                   │<──────────────────│
       │                   │                   │ 7. Client polls   │
       │                   │                   │ for messages      │
       │                   │                   │                   │
       │                   │                   │ 8. Return stored  │
       │                   │                   │ messages          │
       │                   │                   │──────────────────>│
```

#### 3. Implementation of Client Message Polling

```javascript
// Frontend implementation in api-client.js

/**
 * The frontend client checks for new messages every 3 seconds by polling
 * the /api/receive endpoint with its client_id. When messages are received,
 * they are displayed in the chat UI and acknowledged to prevent receiving
 * them again in future polls.
 * 
 * This polling approach was chosen for simplicity and compatibility across
 * different browsers and network configurations, avoiding the complexity of
 * WebSockets or server-sent events.
 */

// Set up polling for new messages
const pollInterval = 3000; // 3 seconds
let poller = null;

function startPolling(clientId) {
  if (poller) clearInterval(poller);
  
  poller = setInterval(async () => {
    try {
      // 1. Request new messages
      const response = await fetch(`/api/receive?client_id=${clientId}`);
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      
      const messages = await response.json();
      if (!messages.length) return; // No new messages
      
      // 2. Process received messages
      messages.forEach(msg => {
        // Add message to UI
        addMessageToChat(msg);
      });
      
      // 3. Acknowledge messages to prevent re-receiving them
      await fetch('/api/receive/acknowledge', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          client_id: clientId,
          message_ids: messages.map(m => m.id)
        })
      });
    } catch (error) {
      console.error('Error polling for messages:', error);
      // Implement exponential backoff strategy for failed requests
    }
  }, pollInterval);
  
  return () => clearInterval(poller); // Return cleanup function
}
```

#### 4. Agent Bridge Message Handling

```python
# Backend implementation in agent_bridge.py

@app.route('/api/send', methods=['POST'])
def handle_send():
    """Handle messages sent from clients"""
    try:
        data = request.json
        message_text = data.get('message', '')
        conversation_id = data.get('conversation_id') or str(uuid.uuid4())
        sender_name = data.get('sender_name', 'Anonymous')
        
        # 1. Log the incoming message
        log_message(conversation_id, 'client_to_agent', sender_name, message_text)
        
        # 2. Check for special command prefixes
        if message_text.startswith('@'):
            # Handle @mention to route message to another agent
            try:
                target_agent_id, msg_content = message_text[1:].split(' ', 1)
                
                # 3. Forward message to the target agent
                result = send_to_agent(target_agent_id, msg_content, conversation_id, 
                                       {'sender_name': sender_name})
                
                return jsonify({
                    'status': 'success',
                    'message': 'Message forwarded to agent',
                    'agent_id': target_agent_id,
                    'conversation_id': conversation_id,
                    'response': result
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Error sending message to agent: {str(e)}',
                    'conversation_id': conversation_id
                })
        elif message_text.startswith('/query') or message_text.startswith('# '):
            # Handle direct query to Claude
            query_text = message_text[7:] if message_text.startswith('/query') else message_text[2:]
            
            # 4. Call Claude API with the query
            response = call_claude(
                prompt=query_text.strip(),
                additional_context="",
                conversation_id=conversation_id,
                current_path="direct_query",
                system_prompt=None  # Uses default agent prompt
            )
            
            # 5. Store response for client to retrieve
            store_message_for_client(
                client_id=request.headers.get('X-Client-ID'),
                message={
                    'id': str(uuid.uuid4()),
                    'text': response or "Error calling Claude",
                    'from_agent': AGENT_ID,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Query processed',
                'conversation_id': conversation_id
            })
        else:
            # Regular message processing
            # 6. Call Claude with the message
            improved_message = message_text
            if IMPROVE_MESSAGES:
                improved_message = improve_message(message_text, conversation_id, 'client_message')
            
            response = call_claude(
                prompt=improved_message,
                additional_context="",
                conversation_id=conversation_id,
                current_path="regular_message"
            )
            
            # 7. Store response for client to retrieve
            store_message_for_client(
                client_id=request.headers.get('X-Client-ID'),
                message={
                    'id': str(uuid.uuid4()),
                    'text': response or "Error processing message",
                    'from_agent': AGENT_ID,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Message processed',
                'conversation_id': conversation_id
            })
            
    except Exception as e:
        print(f"Error in handle_send: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500 
```

## Complete API Reference

This section provides a comprehensive reference of all API endpoints with detailed request and response formats that connect the frontend and backend components.

### Registry API

#### Agent Registration

**Endpoint**: `/register`  
**Method**: POST  
**Description**: Registers an agent with the global registry

**Request Format**:
```json
{
  "agent_id": "agent_name",
  "agent_url": "https://agent-hostname:port",
  "api_url": "https://agent-hostname:port/api"
}
```

**Response Format**:
```json
{
  "status": "registered",
  "agent_id": "agent_name"
}
```

**Error Responses**:
- `400 Bad Request`: Missing required fields
- `409 Conflict`: Agent ID already registered

#### Agent Lookup

**Endpoint**: `/lookup/<id>`  
**Method**: GET  
**Description**: Retrieve URL for a specific agent

**Parameters**:
- `id`: Agent ID to look up (in URL path)

**Response Format**:
```json
{
  "agent_id": "agent_name",
  "agent_url": "https://agent-hostname:port",
  "api_url": "https://agent-hostname:port/api",
  "status": "active"
}
```

**Error Responses**:
- `404 Not Found`: Agent not found in registry

#### List Agents

**Endpoint**: `/list`  
**Method**: GET  
**Description**: List all registered agents

**Response Format**:
```json
{
  "agent1": "https://agent1-hostname:port",
  "agent2": "https://agent2-hostname:port",
  "agent_status": {
    "agent1": {
      "alive": true,
      "assigned_to": "client1",
      "last_update": "2023-11-17T14:22:31.456Z",
      "api_url": "https://agent1-hostname:port/api"
    },
    "agent2": {
      "alive": true,
      "assigned_to": null,
      "last_update": "2023-11-17T14:24:12.789Z",
      "api_url": "https://agent2-hostname:port/api"
    }
  }
}
```

#### Client Allocation

**Endpoint**: `/api/allocate`  
**Method**: POST  
**Description**: Allocate an agent to a client

**Request Format**:
```json
{
  "client_id": "unique_client_id",
  "userProfile": {
    "name": "User Name",
    "email": "user@example.com",
    "picture": "https://profile-picture-url.com/image.jpg"
  }
}
```

**Response Format**:
```json
{
  "status": "success",
  "agent_url": "https://agent-hostname:port",
  "api_url": "https://agent-hostname:port/api",
  "message": "Agent agent_name assigned to username"
}
```

**Error Responses**:
- `400 Bad Request`: Missing client_id or userProfile
- `503 Service Unavailable`: No available agents

#### Check User

**Endpoint**: `/api/check-user`  
**Method**: POST  
**Description**: Check if a user exists in the registry

**Request Format**:
```json
{
  "client_id": "unique_client_id"
}
```

**Response Format**:
```json
{
  "exists": true,
  "agent_id": "assigned_agent_id",
  "api_url": "https://agent-hostname:port/api"
}
```

#### User Sign-up

**Endpoint**: `/api/signup`  
**Method**: POST  
**Description**: Register a new user

**Request Format**:
```json
{
  "client_id": "unique_client_id",
  "userProfile": {
    "name": "User Name",
    "email": "user@example.com",
    "picture": "https://profile-picture-url.com/image.jpg"
  }
}
```

**Response Format**:
```json
{
  "status": "success",
  "message": "User registered successfully"
}
```

### Agent API

#### Send Message

**Endpoint**: `/api/send`  
**Method**: POST  
**Description**: Send a message to an agent

**Request Format**:
```json
{
  "message": "Hello, agent!",
  "conversation_id": "abc123def456",
  "sender_name": "User Name"
}
```

**Response Format**:
```json
{
  "status": "success",
  "message": "Message processed",
  "conversation_id": "abc123def456"
}
```

**Error Responses**:
- `400 Bad Request`: Missing message content
- `500 Internal Server Error`: Error processing message

#### Receive Messages

**Endpoint**: `/api/receive`  
**Method**: GET  
**Description**: Poll for new messages for a specific client

**Query Parameters**:
- `client_id`: The client's unique identifier

**Response Format**:
```json
[
  {
    "id": "msg123",
    "text": "This is a response from the agent",
    "from_agent": "agent_name",
    "conversation_id": "abc123def456",
    "timestamp": "2023-11-17T14:30:45.123Z"
  },
  {
    "id": "msg124",
    "text": "This is another message",
    "from_agent": "agent_name",
    "conversation_id": "abc123def456",
    "timestamp": "2023-11-17T14:31:12.456Z"
  }
]
```

#### Acknowledge Messages

**Endpoint**: `/api/receive/acknowledge`  
**Method**: POST  
**Description**: Acknowledge receipt of messages to prevent re-delivery

**Request Format**:
```json
{
  "client_id": "unique_client_id",
  "message_ids": ["msg123", "msg124"]
}
```

**Response Format**:
```json
{
  "status": "success",
  "acknowledged": 2
}
```

#### Agent-to-Agent Communication

**Endpoint**: `/a2a`  
**Method**: POST  
**Description**: Direct agent-to-agent communication

**Request Format**:
```json
{
  "content": {
    "type": "text",
    "text": "Message from another agent"
  },
  "sender": "agent1_url",
  "metadata": {
    "conversation_id": "abc123def456",
    "sender_name": "Agent 1"
  }
}
```

**Response Format**:
```json
{
  "content": {
    "type": "text",
    "text": "Response to the message"
  },
  "sender": "agent2_url",
  "metadata": {
    "conversation_id": "abc123def456",
    "processed": true
  }
}
```

### Error Handling

All API endpoints follow a consistent error handling pattern:

**Standard Error Response Format**:
```json
{
  "status": "error",
  "message": "Description of the error",
  "code": "ERROR_CODE"
}
```

**Common Error Codes**:
- `INVALID_REQUEST`: Missing or invalid parameters
- `AGENT_NOT_FOUND`: Requested agent not found in registry
- `CLIENT_NOT_FOUND`: Client ID not recognized
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable
- `ANTHROPIC_API_ERROR`: Error when calling Claude API
- `INTERNAL_ERROR`: Unexpected server error

**Error Handling Strategy**:
1. Frontend catches all API errors and displays appropriate user messages
2. For transient errors, automatic retries with exponential backoff
3. Connection errors trigger reconnection attempts
4. Authentication errors redirect to login page

## Key Processes

### User Registration and Authentication

The user registration and authentication process follows these steps:

1. **Google OAuth Authentication**:
   ```
   ┌─────────────┐      ┌────────────┐     ┌────────────┐
   │  Frontend   │      │  Google    │     │  Registry  │
   └──────┬──────┘      └─────┬──────┘     └─────┬──────┘
          │                   │                  │
          │ 1. Initiate OAuth │                  │
          │ Sign-in           │                  │
          │ (GoogleAuth)      │                  │
          │─────────────────>│                  │
          │                   │                  │
          │ 2. Google OAuth   │                  │
          │ Sign-in UI        │                  │
          │<─────────────────│                  │
          │                   │                  │
          │ 3. User consents  │                  │
          │─────────────────>│                  │
          │                   │                  │
          │ 4. Return tokens  │                  │
          │ and user profile  │                  │
          │<─────────────────│                  │
          │                   │                  │
          │ 5. Store profile  │                  │
          │ in localStorage   │                  │
          │                   │                  │
          │ 6. Generate       │                  │
          │ client_id         │                  │
          │                   │                  │
          │ 7. POST /api/signup                 │
          │─────────────────────────────────────>│
          │                   │                  │
          │ 8. Success response                  │
          │<─────────────────────────────────────│
          │                   │                  │
   ```

2. **Client ID Generation and Storage**:
   - A unique client ID is generated for each user on first login
   - The client ID is stored in localStorage for persistence
   - All subsequent API calls include this client ID
   - Example client ID generation:
     ```javascript
     // Generate client ID on first login
     if (!localStorage.getItem('client_id')) {
       const clientId = 'client_' + Math.random().toString(36).substring(2, 15);
       localStorage.setItem('client_id', clientId);
     }
     ```

3. **Session Management**:
   - Sessions persist through browser restarts via localStorage
   - No server-side session state is maintained
   - The user profile and client ID are the primary identifiers

### Agent Allocation

The process of allocating an agent to a user:

1. **Initial Allocation**:
   ```
   ┌─────────────┐      ┌────────────┐      ┌────────────┐
   │  Frontend   │      │  Registry  │      │   Agent    │
   └──────┬──────┘      └─────┬──────┘      └─────┬──────┘
          │                   │                   │
          │ 1. POST /api/allocate                │
          │ (client_id + userProfile)            │
          │──────────────────>│                  │
          │                   │                  │
          │                   │ 2. Find available│
          │                   │ agent           │
          │                   │                  │
          │                   │ 3. Update agent  │
          │                   │ assignment      │
          │                   │                  │
          │ 4. Return agent URL & API URL       │
          │<──────────────────│                  │
          │                   │                  │
          │ 5. Store agent    │                  │
          │ URLs in memory    │                  │
          │                   │                  │
          │ 6. Connect to     │                  │
          │ assigned agent    │                  │
          │─────────────────────────────────────>│
          │                   │                  │
          │ 7. Agent ready    │                  │
          │<─────────────────────────────────────│
          │                   │                  │
   ```

2. **Allocation Persistence**:
   - Registry maintains a mapping of client names to agent IDs
   - This mapping persists in MongoDB
   - Users are consistently assigned to the same agent across sessions
   - When a user returns, they're automatically reconnected to their assigned agent

3. **Agent Load Balancing**:
   - New users are assigned to the least loaded agent
   - Random selection among available agents
   - Once assigned, the relationship is permanent until manually changed

### Message Routing

Detailed message routing process between frontend, registry and agents:

1. **Direct Message to Assigned Agent**:
   - User sends message via frontend
   - Message is sent directly to the assigned agent's API endpoint
   - Response is stored for retrieval via polling
   - Implementation in api-client.js:
     ```javascript
     async sendMessage(targetUrl, message, agentId) {
       // Format message with @mentions if needed
       let formattedMessage = hasExistingMention ? 
         message : (agentId ? `@${agentId} ${message}` : message);
       
       // Send to agent API
       const response = await fetch(targetUrl, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           message: formattedMessage,
           conversation_id: this.conversationId,
           sender_name: senderName
         })
       });
       
       // Process response
       const data = await response.json();
       this.conversationId = data.conversation_id;
       return data;
     }
     ```

2. **Message to Another Agent (Using @mentions)**:
   - User sends message with @agent_name prefix
   - Assigned agent receives message and extracts target agent name
   - Agent looks up target agent URL from registry
   - Message is forwarded to target agent
   - Response flows back through original agent
   - Frontend polls for response

3. **Polling Implementation**:
   - Frontend polls `/api/receive` endpoint every 3 seconds
   - Messages are displayed when received
   - Messages are acknowledged to prevent re-delivery
   - Implementation in script.js:
     ```javascript
     function pollForMessages(clientId) {
       return setInterval(async () => {
         try {
           // Request new messages
           const response = await fetch(`/api/receive?client_id=${clientId}`);
           const messages = await response.json();
           
           if (messages.length) {
             // Display messages
             messages.forEach(msg => renderMessage(msg));
             
             // Acknowledge receipt
             await fetch('/api/receive/acknowledge', {
               method: 'POST',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify({
                 client_id: clientId,
                 message_ids: messages.map(m => m.id)
               })
             });
           }
         } catch (error) {
           console.error('Error polling for messages:', error);
         }
       }, 3000);
     }
     ```

### Inter-Agent Communication

The process for communication between agents:

1. **Agent-to-Agent Protocol**:
   - Uses a custom protocol defined in the A2AServer and A2AClient classes
   - Messages are sent via HTTP POST to the `/a2a` endpoint
   - Authentication is implicit through registry lookups
   - Supports both text and error message types

2. **Message Structure**:
   ```python
   class Message:
     def __init__(self, content, sender, metadata=None):
       self.content = content  # TextContent or ErrorContent
       self.sender = sender    # Sender URL
       self.metadata = metadata or {}  # Additional metadata
   
   class TextContent:
     def __init__(self, text):
       self.type = "text"
       self.text = text
   
   class ErrorContent:
     def __init__(self, error):
       self.type = "error"
       self.error = error
   ```

3. **Communication Flow**:
   ```
   Agent A                  Registry                  Agent B
      |                        |                        |
      | Need to send to B      |                        |
      |----------------------->|                        |
      |                        |                        |
      | Returns B's URL        |                        |
      |<-----------------------|                        |
      |                        |                        |
      | POST to B's /a2a endpoint                      |
      |----------------------------------------------->|
      |                        |                        |
      |                        |                        | Process
      |                        |                        | message
      |                        |                        |
      | Response                                        |
      |<-----------------------------------------------|
      |                        |                        |
   ```

4. **Message Processing**:
   - Each agent implements a `handle_message` method
   - Messages are processed based on content type and sender
   - Special commands are handled differently
   - For @mentions, the message is forwarded to the target agent
   - Regular messages are sent to Claude for processing 