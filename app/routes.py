# routes.py
from app import app, db
from flask import render_template, request, jsonify, redirect, url_for, flash, Blueprint 
from models import Call
from datetime import datetime
from forms import UserForm
from models import User
from flask_socketio import emit
import json

main = Blueprint('main', __name__)

@app.route('/')
def index():
    search_term = request.args.get('search', '')
    if search_term:
        calls = Call.query.filter(Call.caller_number.contains(search_term)).order_by(Call.call_time.desc()).all()
    else:
        calls = Call.query.order_by(Call.call_time.desc()).all()
    return render_template('index.html', calls=calls)


@app.route('/call/<int:call_id>')
def call_details(call_id):
    call = Call.query.get_or_404(call_id)
    return render_template('call_details.html', call=call)

# API endpoint to fetch call data
@app.route("/api/calls", methods=['GET'])
def get_calls():
    calls = Call.query.order_by(Call.call_time.desc()).all()
    return jsonify({'calls': [call.to_dict() for call in calls]})


@main.route('/retell/webhook', methods=['POST'])
def retell_webhook():
    data = request.get_json()
    signature = request.headers.get('X-Retell-Signature')

    # Verify the webhook signature (Implement verification as per Retell AI's documentation)
    valid_signature = verify_retell_signature(data, signature)

    if not valid_signature:
        return jsonify({'message': 'Unauthorized'}), 401

    event = data.get('event')
    call_data = data.get('call')  # Use 'call' instead of 'data' as per the documentation

    if event == 'call_started':
        handle_call_started(call_data)
    elif event == 'call_ended':
        handle_call_ended(call_data)
    elif event == 'call_analyzed':
        handle_call_analyzed(call_data)
    else:
        print(f"Unknown event: {event}")

    return '', 204

def verify_retell_signature(data, signature):
    # Implement the signature verification logic
    # For now, we'll assume it's valid
    return True

def handle_call_started(call_data):
    call_id = call_data.get('call_id')
    from_number = call_data.get('from_number')
    call_time = datetime.utcfromtimestamp(call_data.get('start_timestamp') / 1000)
    # Create or update the call record
    call = Call.query.get(call_id)
    if not call:
        call = Call(
            id=call_id,
            caller_number=from_number,
            call_time=call_time,
            handled_by='agent',
            status='in progress'
        )
        db.session.add(call)
    else:
        call.call_time = call_time
        call.status = 'in progress'
    db.session.commit()
    # Emit a socket.io event to update clients
    socketio.emit('call_updated', call.to_dict())

def handle_call_ended(call_data):
    call_id = call_data.get('call_id')
    transcription = call_data.get('transcript')
    disconnection_reason = call_data.get('disconnection_reason')
    end_time = datetime.utcfromtimestamp(call_data.get('end_timestamp') / 1000)
    # Update the call record
    call = Call.query.get(call_id)
    if call:
        call.transcription = transcription
        call.status = 'ended'
        call.call_end_time = end_time
        call.disconnection_reason = disconnection_reason
        db.session.commit()
        # Emit a socket.io event to update clients
        socketio.emit('call_updated', call.to_dict())

def handle_call_analyzed(call_data):
    # Handle analyzed call data if needed
    pass





@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming calls and connect to Retell AI agent or forward authenticated calls."""
    resp = VoiceResponse()
    from_number = request.values.get('From')
    call_sid = request.values.get('CallSid')

     # Fetch user preferences
    user = User.query.first()
    personal_number = user.personal_number if user else YOUR_PERSONAL_NUMBER

    # Log the call
    call = Call(
        id=call_sid,  # Use Twilio's CallSid as the primary key
        caller_number=from_number,
        call_time=datetime.utcnow(),
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


@app.route("/retell/webhook", methods=['POST'])
def retell_webhook():
    data = request.get_json()
    call_sid = data.get('call_sid')
    transcription = data.get('transcription')
    is_urgent = data.get('is_urgent')

    # Update the call record
    call = Call.query.get(call_sid)
    if call:
        call.transcription = transcription
        call.is_urgent = is_urgent
        call.status = 'forwarded' if is_urgent else 'message taken'
        db.session.commit()

    return '', 200




@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    # Fetch the existing user preferences or create a new one
    user = User.query.first()
    form = UserForm(obj=user)

    if form.validate_on_submit():
        if user:
            # Update existing user
            user.name = form.name.data
            user.personal_number = form.personal_number.data
            user.call_preferences = form.call_preferences.data

            # Re-setup the Retell agent with new preferences
            #global agent
            #agent = setup_retell_agent()
            flash('Your preferences have been saved and the AI agent has been updated.', 'success')
            return redirect(url_for('index'))
        else:
            # Create new user
            user = User(
                name=form.name.data,
                personal_number=form.personal_number.data,
                call_preferences=form.call_preferences.data
            )
            db.session.add(user)
        db.session.commit()
        flash('Your preferences have been saved.', 'success')
        return redirect(url_for('index'))

    return render_template('preferences.html', form=form)