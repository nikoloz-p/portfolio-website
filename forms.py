from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length 


class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(min=3, max=100)])
    image = StringField('Image Path', validators=[DataRequired()])
    width = StringField("Image Width", validators=[DataRequired()])
    height = StringField("Image Height", validators=[DataRequired()])
    description = StringField("Project Description", validators=[DataRequired(), Length(min=3, max=100)])
    grid_row = StringField('Grid Row (e.g., "1 / span 2")', validators=[DataRequired()])
    grid_column = StringField('Grid Column (e.g., "3 / span 1")', validators=[DataRequired()])
    submit = SubmitField('Add Project', validators=[DataRequired()])