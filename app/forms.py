from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, DateField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 255)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(0, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(0, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    headline = StringField('Professional Headline', validators=[Optional(), Length(0, 200)])
    summary = TextAreaField('Summary', validators=[Optional(), Length(0, 2000)])
    location = StringField('Location', validators=[Optional(), Length(0, 200)])
    industry = StringField('Industry', validators=[Optional(), Length(0, 100)])
    current_position = StringField('Current Position', validators=[Optional(), Length(0, 200)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'), ('Prefer not to say', 'Prefer not to say')], validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(0, 20)])
    privacy_level = SelectField('Privacy Level', choices=[('Public', 'Public'), ('Connections Only', 'Connections Only'), ('Private', 'Private')], default='Public')
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    cover_photo = FileField('Cover Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')

class PostForm(FlaskForm):
    content = TextAreaField('What\'s on your mind?', validators=[DataRequired(), Length(1, 3000)])
    post_type = SelectField('Post Type', choices=[('text', 'Text'), ('image', 'Image'), ('video', 'Video'), ('link', 'Link'), ('document', 'Document')], default='text')
    media_file = FileField('Upload Media', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx'], 'Invalid file type!')])
    link_url = StringField('Link URL', validators=[Optional(), Length(0, 1000)])
    link_title = StringField('Link Title', validators=[Optional(), Length(0, 500)])
    link_description = TextAreaField('Link Description', validators=[Optional(), Length(0, 1000)])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('connections', 'Connections Only'), ('private', 'Private')], default='public')
    allow_comments = BooleanField('Allow Comments', default=True)
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Write a comment...', validators=[DataRequired(), Length(1, 1000)])
    submit = SubmitField('Comment')

class MessageForm(FlaskForm):
    recipient_id = HiddenField(validators=[DataRequired()])
    content = TextAreaField('Type your message...', validators=[DataRequired(), Length(1, 2000)])
    message_type = SelectField('Type', choices=[('text', 'Text'), ('image', 'Image'), ('file', 'File')], default='text')
    media_file = FileField('Upload File', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'pdf', 'doc', 'docx'], 'Invalid file type!')])
    submit = SubmitField('Send')

class WorkExperienceForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(1, 200)])
    job_title = StringField('Job Title', validators=[DataRequired(), Length(1, 200)])
    employment_type = SelectField('Employment Type', choices=[
        ('Full-time', 'Full-time'), ('Part-time', 'Part-time'), ('Self-employed', 'Self-employed'),
        ('Freelance', 'Freelance'), ('Contract', 'Contract'), ('Internship', 'Internship')
    ], default='Full-time')
    location = StringField('Location', validators=[Optional(), Length(0, 200)])
    location_type = SelectField('Location Type', choices=[('On-site', 'On-site'), ('Remote', 'Remote'), ('Hybrid', 'Hybrid')], default='On-site')
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    is_current = BooleanField('I currently work here')
    description = TextAreaField('Description', validators=[Optional(), Length(0, 2000)])
    submit = SubmitField('Save Experience')

class EducationForm(FlaskForm):
    institution_name = StringField('Institution Name', validators=[DataRequired(), Length(1, 200)])
    degree_type = SelectField('Degree Type', choices=[
        ('High School', 'High School'), ('Associate', 'Associate'), ('Bachelor', 'Bachelor'),
        ('Master', 'Master'), ('Doctorate', 'Doctorate'), ('Certificate', 'Certificate'), ('Other', 'Other')
    ], validators=[Optional()])
    field_of_study = StringField('Field of Study', validators=[Optional(), Length(0, 200)])
    grade = StringField('Grade', validators=[Optional(), Length(0, 10)])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 2000)])
    submit = SubmitField('Save Education')

class ConnectionRequestForm(FlaskForm):
    message = TextAreaField('Personal Message', validators=[Optional(), Length(0, 500)])
    submit = SubmitField('Send Request')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(1, 500)])
    search_type = SelectField('Search Type', choices=[('all', 'All'), ('people', 'People'), ('posts', 'Posts'), ('companies', 'Companies')], default='all')
    submit = SubmitField('Search')
