from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class UserForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    personal_number = StringField('Personal Phone Number', validators=[DataRequired()])
    call_preferences = TextAreaField('Types of Calls You Care About', validators=[DataRequired()])
    submit = SubmitField('Save Preferences')
