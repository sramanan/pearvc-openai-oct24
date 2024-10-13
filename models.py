# models.py
from app import db




class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caller_number = db.Column(db.String(20))
    call_time = db.Column(db.DateTime)
    transcription = db.Column(db.Text)
    is_urgent = db.Column(db.Boolean)
    handled_by = db.Column(db.String(50))
    status = db.Column(db.String(20))
    disconnection_reason = db.Column(db.String(50))
    call_type = db.Column(db.String(50))
    call_message = db.Column(db.String(100))

    def __repr__(self):
        return f'<Call {self.id} - {self.caller_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'caller_number': self.caller_number,
            'call_time': self.call_time.isoformat(),
            'transcription': self.transcription,
            'is_urgent': self.is_urgent,
            'handled_by': self.handled_by,
            'status': self.status,
            'disconnection_reason': self.disconnection_reason
        }


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    personal_number = db.Column(db.String(20))
    call_preferences = db.Column(db.Text)  # JSON string or plaintext

    def __repr__(self):
        return f'<User {self.name}>'