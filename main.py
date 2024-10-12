from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.voice_response import VoiceResponse, Dial
from retell import Retell
from retell.resources.llm import LlmResponse
from retell.resources.agent import AgentResponse
from datetime import datetime

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calls.db'  # Use PostgreSQL or MySQL for production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# Define the Call model
class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caller_number = db.Column(db.String(20))
    call_time = db.Column(db.DateTime, default=datetime.utcnow)
    transcription = db.Column(db.Text)
    is_urgent = db.Column(db.Boolean)
    handled_by = db.Column(db.String(50))  # 'agent' or 'direct'
    status = db.Column(db.String(20))  # 'forwarded', 'message taken', etc.

    def to_dict(self):
        return {
            'id': self.id,
            'caller_number': self.caller_number,
            'call_time': self.call_time.isoformat(),
            'transcription': self.transcription,
            'is_urgent': self.is_urgent,
            'handled_by': self.handled_by,
            'status': self.status
        }

# Create the database tables
with app.app_context():
    db.create_all()

# Create the LLM and Agent
def setup_retell_agent():
    # ... (same as before)

# Set up the Retell agent
agent = setup_retell_agent()

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming calls and connect to Retell AI agent or forward authenticated calls."""
    resp = VoiceResponse()
    from_number = request.values.get('From')

    # Log the call
    call = Call(
        caller_number=from_number,
        handled_by='direct' if from_number in AUTHENTICATED_NUMBERS else 'agent',
        status='forwarded' if from_number in AUTHENTICATED_NUMBERS else 'in progress'
    )
    db.session.add(call)
    db.session.commit()

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

# API endpoint to fetch call data
@app.route("/api/calls", methods=['GET'])
def get_calls():
    calls = Call.query.order_by(Call.call_time.desc()).all()
    return {'calls': [call.to_dict() for call in calls]}

if __name__ == "__main__":
    app.run(debug=True)
