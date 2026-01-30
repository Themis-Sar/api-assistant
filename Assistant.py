import os
import json
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from anthropic import Anthropic
from dotenv import load_dotenv

# =============================

load_dotenv()
# =============================


username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD" ) 
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
token_url = os.getenv("TOKEN_URL")
api_url = os.getenv("API_URL")

# =============================
# Flask setup
# =============================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Anthropic client
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# Your API client functions
# =============================
def get_access_token():
    data = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    response = requests.post(token_url, data=data, auth=(client_id, client_secret))
    response.raise_for_status()
    return response.json().get("access_token")

def get_schools(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{api_url}/group/main", headers=headers)
    r.raise_for_status()
    return r.json()

def get_school_rooms(access_token, school_uuid):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{api_url}/group/{school_uuid}/subgroup/3", headers=headers)
    r.raise_for_status()
    return r.json()

def get_room_sensors(access_token, room_uuid):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{api_url}/group/{room_uuid}/resource", headers=headers)
    r.raise_for_status()
    return r.json()

def get_sensor_latest_value(access_token, sensor_uuid):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{api_url}/resource/{sensor_uuid}/latest", headers=headers)
    r.raise_for_status()
    return r.json()

# =============================
# External API Client
# =============================
class ExternalAPIClient:
    """Your school/room/sensor API handler"""
    def __init__(self):
        self.token = get_access_token()

    def fetch_schools(self):
        return get_schools(self.token)

    def fetch_rooms(self, school_uuid):
        return get_school_rooms(self.token, school_uuid)

    def fetch_sensors(self, room_uuid):
        return get_room_sensors(self.token, room_uuid)

    def fetch_sensor_value(self, sensor_uuid):
        return get_sensor_latest_value(self.token, sensor_uuid)

# =============================
# Fixed Claude Chatbot
# =============================
class ClaudeChatbot:
    """Claude AI wrapper with seamless API integration"""
    def __init__(self):
        self.api_client = ExternalAPIClient()
        self.conversation_history = []

    def call_claude_api(self, user_message, api_data=None):
        try:
            if api_data is None:
                # First call - ask for JSON if API needed
                system_prompt = """You are a helpful assistant for a school IoT API.

If the user asks for schools, rooms, sensors, or sensor values, respond with a JSON object in this format:
{
  "needsAPI": true,
  "apiType": "schools|rooms|sensors|values",
  "params": {"school_uuid": "...", "room_uuid": "...", "sensor_uuid": "..."}
}

If no API is needed, respond normally with helpful text."""
            else:
                # Second call - format the API data nicely
                system_prompt = f"""You are a helpful assistant for a school IoT API.

The user asked: "{user_message}"

Here is the API data you requested:
{json.dumps(api_data, indent=2)}

Please present this data in a clear, well-formatted way. Use tables, lists, and markdown formatting to make it easy to read. Do NOT return JSON - return formatted text."""

            # Build messages for the conversation
            messages = []
            
            # Add conversation history (last few messages for context)
            recent_history = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return "Sorry, there was an error processing your request."

    def process_message(self, user_message):
        """Process user message with seamless API integration"""
        self.conversation_history.append({"role": "user", "content": user_message})

        # First, get Claude's response
        claude_response = self.call_claude_api(user_message)
        
        # Check if Claude wants to make an API call
        try:
            parsed_response = json.loads(claude_response.strip())
            if parsed_response.get("needsAPI"):
                # Fetch the requested data
                api_data = self.fetch_external_data(
                    parsed_response["apiType"], 
                    parsed_response.get("params", {})
                )
                
                # Get Claude's final response with the API data
                final_response = self.call_claude_api(user_message, api_data)
                self.conversation_history.append({"role": "assistant", "content": final_response})
                return final_response
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON parsing error: {e}")
            # If it's not a JSON API request, just return the response
            pass
        except Exception as e:
            logger.error(f"API processing error: {e}")
            # Return the original response if API processing fails
            pass

        # Regular conversation - no API needed
        self.conversation_history.append({"role": "assistant", "content": claude_response})
        return claude_response

    def fetch_external_data(self, api_type, params):
        """Fetch data from external API based on type and parameters"""
        try:
            if api_type == "schools":
                return self.api_client.fetch_schools()
            elif api_type == "rooms":
                school_uuid = params.get("school_uuid")
                if not school_uuid:
                    return {"error": "School UUID required for fetching rooms"}
                return self.api_client.fetch_rooms(school_uuid)
            elif api_type == "sensors":
                room_uuid = params.get("room_uuid")
                if not room_uuid:
                    return {"error": "Room UUID required for fetching sensors"}
                return self.api_client.fetch_sensors(room_uuid)
            elif api_type == "values":
                sensor_uuid = params.get("sensor_uuid")
                if not sensor_uuid:
                    return {"error": "Sensor UUID required for fetching values"}
                return self.api_client.fetch_sensor_value(sensor_uuid)
            else:
                return {"error": f"Unknown API type: {api_type}"}
        except Exception as e:
            logger.error(f"API fetch error: {e}")
            return {"error": f"Failed to fetch {api_type}: {str(e)}"}

# =============================
# Routes
# =============================
chatbot = ClaudeChatbot()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({"error": "Message required"}), 400
        response = chatbot.process_message(user_message)
        return jsonify({"response": response, "conversation": chatbot.conversation_history})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "Internal error"}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    global chatbot
    chatbot = ClaudeChatbot()
    return jsonify({"status": "cleared"})

# =============================
# HTML Template
# =============================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School IoT Chatbot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .message-animation {
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="max-w-4xl mx-auto h-screen flex flex-col">
        <!-- Header -->
        <div class="bg-blue-600 text-white p-4 shadow-lg">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-xl font-semibold flex items-center gap-2">
                        🏫 School IoT Assistant
                    </h1>
                    <p class="text-blue-100 text-sm mt-1">Ask about schools, rooms, sensors, and real-time data!</p>
                </div>
                <button id="clearBtn" class="bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded text-sm">
                    Clear Chat
                </button>
            </div>
        </div>

        <!-- Messages -->
        <div id="messages" class="flex-1 overflow-y-auto p-4 space-y-4">
            <div class="flex gap-3 message-animation">
                <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                    🤖
                </div>
                <div class="bg-gray-100 rounded-lg p-3 max-w-3xl">
                    <p>Hello! I'm your School IoT Assistant. I can help you with:</p>
                    <ul class="mt-2 text-sm text-gray-600">
                        <li>• List all schools in the system</li>
                        <li>• Show rooms in specific schools</li>
                        <li>• Display sensors in rooms</li>
                        <li>• Get real-time sensor readings</li>
                    </ul>
                    <p class="mt-2 text-sm">Try asking: "Show me all schools" or "What sensors are available?"</p>
                </div>
            </div>
        </div>

        <!-- Input -->
        <div class="border-t bg-white p-4">
            <div class="flex gap-2">
                <input 
                    id="messageInput" 
                    type="text" 
                    placeholder="Ask me about schools, rooms, sensors, or data..."
                    class="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                <button 
                    id="sendBtn" 
                    class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                    Send
                </button>
            </div>
            <div class="mt-2 text-sm text-gray-600">
                💡 Make sure to set your API credentials in environment variables or update the code
            </div>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const clearBtn = document.getElementById('clearBtn');

        let isLoading = false;

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `flex gap-3 message-animation ${isUser ? 'justify-end' : ''}`;
            
            messageDiv.innerHTML = `
                <div class="flex gap-2 max-w-3xl ${isUser ? 'flex-row-reverse' : ''}">
                    <div class="w-8 h-8 ${isUser ? 'bg-blue-500' : 'bg-gray-500'} rounded-full flex items-center justify-center">
                        ${isUser ? '👤' : '🤖'}
                    </div>
                    <div class="${isUser ? 'bg-blue-500 text-white' : 'bg-gray-100'} rounded-lg p-3">
                        <div class="whitespace-pre-wrap">${content}</div>
                    </div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addLoadingMessage() {
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'loading-message';
            loadingDiv.className = 'flex gap-3 message-animation';
            loadingDiv.innerHTML = `
                <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                    🤖
                </div>
                <div class="bg-gray-100 rounded-lg p-3">
                    <div class="flex items-center gap-2">
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                        <span>Fetching data...</span>
                    </div>
                </div>
            `;
            messagesDiv.appendChild(loadingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function removeLoadingMessage() {
            const loadingMsg = document.getElementById('loading-message');
            if (loadingMsg) {
                loadingMsg.remove();
            }
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || isLoading) return;

            isLoading = true;
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';

            // Add user message
            addMessage(message, true);
            messageInput.value = '';

            // Add loading message
            addLoadingMessage();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message })
                });

                const data = await response.json();
                
                if (response.ok) {
                    removeLoadingMessage();
                    addMessage(data.response);
                } else {
                    removeLoadingMessage();
                    addMessage(`Error: ${data.error}`);
                }
            } catch (error) {
                removeLoadingMessage();
                addMessage('Sorry, there was an error connecting to the server.');
            }

            isLoading = false;
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
            messageInput.focus();
        }

        async function clearConversation() {
            try {
                await fetch('/api/clear', { method: 'POST' });
                // Clear messages except the first welcome message
                const firstMessage = messagesDiv.firstElementChild;
                messagesDiv.innerHTML = '';
                messagesDiv.appendChild(firstMessage);
            } catch (error) {
                console.error('Error clearing conversation:', error);
            }
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        clearBtn.addEventListener('click', clearConversation);
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
'''

# =============================
# Main
# =============================
if __name__ == '__main__':
    print("Starting School IoT Chatbot...")
    print("Make sure to set these environment variables:")
    print("- ANTHROPIC_API_KEY")
    print("- API_USERNAME, API_PASSWORD")
    print("- CLIENT_ID, CLIENT_SECRET")
    print("\nOr update the configuration section in the code.")
    app.run(debug=True, host='0.0.0.0', port=5000)