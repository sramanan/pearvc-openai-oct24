from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Dial
from retell import Retell
from retell.resources.llm import LlmResponse
from retell.resources.agent import AgentResponse

app = Flask(__name__)

# Set your Retell AI API key
RETELL_AI_API_KEY = 'YOUR_RETELL_AI_API_KEY'

# Your personal phone number in E.164 format (e.g., '+1234567890')
YOUR_PERSONAL_NUMBER = '+YOUR_PERSONAL_NUMBER'

# List of authenticated phone numbers (friends and family) in E.164 format
AUTHENTICATED_NUMBERS = ['+15555555555', '+16666666666']

# Initialize Retell AI client
retell_client = Retell(
    api_key=RETELL_AI_API_KEY
)

# Create the LLM and Agent
def setup_retell_agent():
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

# Set up the Retell agent
agent = setup_retell_agent()

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming calls and connect to Retell AI agent or forward authenticated calls."""
    resp = VoiceResponse()
    from_number = request.values.get('From')

    if from_number in AUTHENTICATED_NUMBERS:
        # Forward the call directly to your personal number
        resp.say("Connecting you now.")
        resp.dial(YOUR_PERSONAL_NUMBER)
    else:
        # Connect the call to the Retell AI agent
        dial = Dial()
        dial.sip(f'sip:{agent.agent_sip_address}')
        resp.append(dial)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)