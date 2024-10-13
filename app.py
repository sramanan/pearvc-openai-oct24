# app.py
from flask import Flask, request 
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap  # If using Bootstrap
from flask_cors import CORS

from twilio.twiml.voice_response import VoiceResponse, Dial
from retell import Retell
from retell.resources.llm import LlmResponse
from retell.resources.agent import AgentResponse

from flask_socketio import SocketIO

from extensions import socketio

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)  # If using Bootstrap

# socketio.init_app(app, cors_allowed_origins="*")

from routes import *  # Import routes

# Import routes after initializing app and socketio
from routes import main as main_blueprint
app.register_blueprint(main_blueprint)

# Set your Retell AI API key
RETELL_AI_API_KEY = 'key_0f9377a0e8bcd743c194366bd3f5'

# Your personal phone number in E.164 format (e.g., '+1234567890')
YOUR_PERSONAL_NUMBER = '+19736411770'

# List of authenticated phone numbers (friends and family) in E.164 format
AUTHENTICATED_NUMBERS = ['+15555555555', '+16666666666']

# Initialize Retell AI client
retell_client = Retell(
    api_key=RETELL_AI_API_KEY
)


# Create the LLM and Agent
def setup_retell_agent():
	# Fetch user preferences
    user = User.query.first()
    if not user:
        # Default values if user preferences are not set
        user_name = "Garry Tan"
        call_preferences = "urgent business matters, family emergencies, and calls from known contacts."
        personal_number = YOUR_PERSONAL_NUMBER  # Fallback to the existing variable
    else:
        user_name = user.name
        call_preferences = user.call_preferences
        personal_number = user.personal_number
    # Create the LLM
    llm: LlmResponse = retell_client.llm.create(
        general_prompt="You are an AI receptionist that answers phone calls, determines if they are urgent or important, and decides whether to forward the call or take a message.",
        general_tools=[
            {
                "type": "end_call",
                "name": "end_call",
                "description": "End the call politely when appropriate.",
            },
            {
                "type": "transfer_call",
                "name": "transfer_call",
                "description": "Transfer the call to the personal number if the call is urgent or important.",
                "number": YOUR_PERSONAL_NUMBER,
            },
        ],
        states=[
            {
                "name": "information_collection",
                "state_prompt": "Greet the caller and ask for their name and the purpose of their call.",
                "edges": [
                    {
                        "destination_state_name": "determine_urgency",
                        "description": "Once you have the caller's message, move to determine urgency.",
                    },
                ],
                "tools": []
            },
            {
                "name": "determine_urgency",
                "state_prompt": "Analyze the caller's message to determine if the call is urgent or important. If urgent, transition to 'urgent_call'; if not, transition to 'non_urgent_call'.",
                "edges": [
                    {
                        "destination_state_name": "urgent_call",
                        "description": "If the call is urgent or important, forward the call.",
                    },
                    {
                        "destination_state_name": "non_urgent_call",
                        "description": "If the call is not urgent, take a message.",
                    },
                ],
                "tools": []
            },
            {
                "name": "urgent_call",
                "state_prompt": "Inform the caller that you are connecting them now.",
                "edges": [],
                "tools": [
                    {
                        "type": "transfer_call",
                        "name": "transfer_call",
                        "description": "Transfer the call to the personal number.",
                        "number": YOUR_PERSONAL_NUMBER,
                    },
                ],
            },
            {
                "name": "non_urgent_call",
                "state_prompt": "Politely inform the caller that their message will be delivered promptly.",
                "edges": [],
                "tools": [
                    {
                        "type": "end_call",
                        "name": "end_call",
                        "description": "End the call politely.",
                    },
                ],
            },
        ],
        starting_state="information_collection",
        begin_message="Hello, you've reached [Your Name]'s office."
    )

    # Create the agent and assign the LLM
    agent: AgentResponse = retell_client.agent.create(
        llm_websocket_url=llm.llm_websocket_url,
        voice_id="elevenlabs/eleven_monolingual_v1/Adrian",  # Replace with the correct voice ID
        agent_name="AI Receptionist"
    )

    return agent


# socketio.run(app, port=5000,debug=True, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
	app.run(debug=True, port=os.getenv("PORT", default=5000))

    
    # Run the Flask app

# Set up the Retell agent
#agent = setup_retell_agent()

#print(agent)
