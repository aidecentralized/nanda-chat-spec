# test_agent_bridge.py
import requests
import json
import time
import argparse
import sys

def test_agent_bridge(base_url, verbose=False):
    """Test the agent bridge API endpoints"""
    print(f"Testing agent bridge at {base_url}...")
    
    # Test 1: Health check
    print("\n=== Test 1: Health Check ===")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data}")
            agent_id = data.get('agent_id', 'unknown')
        else:
            print(f"❌ Health check failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return False
    
    # Test 2: Send a simple message
    print("\n=== Test 2: Send a Simple Message ===")
    try:
        payload = {
            "message": "Hello, what's your name?",
            "client_id": "test_client",
            "conversation_id": f"test_conv_{int(time.time())}"
        }
        
        if verbose:
            print(f"Sending request to {base_url}/api/send")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
        response = requests.post(
            f"{base_url}/api/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message sent successfully")
            print(f"Response: {data.get('response', '')[:100]}...")
            conversation_id = data.get('conversation_id')
            print(f"Conversation ID: {conversation_id}")
        else:
            print(f"❌ Message sending failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Message sending failed with error: {e}")
        return False
    
    # Test 3: Send a query
    print("\n=== Test 3: Send a Query ===")
    try:
        payload = {
            "message": "/query What is the current date?",
            "client_id": "test_client",
            "conversation_id": conversation_id
        }
        
        response = requests.post(
            f"{base_url}/api/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query sent successfully")
            print(f"Response: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Query failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query failed with error: {e}")
        return False
    
    # Test 4: Get list of agents
    print("\n=== Test 4: List Agents ===")
    try:
        response = requests.get(f"{base_url}/api/agents/list")
        
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Got agent list successfully")
            print(f"Registered agents: {json.dumps(agents, indent=2)}")
            
            # Find an agent to send a message to
            other_agents = [a for a in agents.keys() if a != agent_id]
            if other_agents:
                test_agent = "adam" #other_agents[0]
                print(f"Found other agent to test: {test_agent}")
                public_urls = {"camcult": "https://3a6b-18-27-114-185.ngrok-free.app",
			       "adam": "https://b5fe-18-27-114-185.ngrok-free.app"}
                
                # Test 5: Send a message to another agent
                print("\n=== Test 5: Send Message to Another Agent ===")
                payload = {
                    "message": f"@{test_agent} Hello from the test script!",
                    "client_id": "test_client",
                    "conversation_id": conversation_id
                }
                
                response = requests.post(
                    f"{base_url}/api/send",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Message to other agent sent successfully")
                    print(f"Response: {data}")
                else:
                    print(f"❌ Message to other agent failed with status code {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                print("⚠️ No other agents found for testing cross-agent communication")
        else:
            print(f"❌ Getting agent list failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Getting agent list failed with error: {e}")
        return False
    
    print("\n=== All tests completed successfully! ===")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test agent bridge API")
    parser.add_argument("--url", required=True, help="Base URL of the agent bridge API (e.g., http://localhost:5000)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    success = test_agent_bridge(args.url, args.verbose)
    if not success:
        sys.exit(1)
