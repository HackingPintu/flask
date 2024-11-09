from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class RepoForm(FlaskForm):
    name = StringField('Repository Name', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Create Repository')
