from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

# Association table for user skills
user_skills = db.Table('user_skills',
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.skill_id'), primary_key=True),
    db.Column('proficiency_level', db.String(20), default='Intermediate'),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Association table for conversation participants
conversation_participants = db.Table('conversation_participants',
    db.Column('conversation_id', db.Integer, db.ForeignKey('conversations.conversation_id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow),
    db.Column('role', db.String(20), default='member')
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('Male', 'Female', 'Other', 'Prefer not to say', name='gender_enum'))
    phone_number = db.Column(db.String(20))
    profile_picture_url = db.Column(db.String(500))
    cover_photo_url = db.Column(db.String(500))
    headline = db.Column(db.String(200))
    summary = db.Column(db.Text)
    location = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    current_position = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    privacy_level = db.Column(db.Enum('Public', 'Connections Only', 'Private', name='privacy_enum'), default='Public')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    posts = relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    work_experiences = relationship('WorkExperience', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    education = relationship('Education', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    skills = relationship('Skill', secondary=user_skills, backref='users')
    sent_messages = relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    conversations = relationship('Conversation', secondary=conversation_participants, backref='participants')

    # Connection relationships
    sent_connections = relationship('Connection', foreign_keys='Connection.requester_id', backref='requester', lazy='dynamic')
    received_connections = relationship('Connection', foreign_keys='Connection.requested_id', backref='requested', lazy='dynamic')

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_connections(self):
        return Connection.query.filter(
            ((Connection.requester_id == self.user_id) | (Connection.requested_id == self.user_id))
            & (Connection.status == 'accepted')
        ).all()

    def is_connected_with(self, user):
        return Connection.query.filter(
            ((Connection.requester_id == self.user_id) & (Connection.requested_id == user.user_id)) |
            ((Connection.requester_id == user.user_id) & (Connection.requested_id == self.user_id))
        ).filter(Connection.status == 'accepted').first() is not None

    def connection_status_with(self, user):
        connection = Connection.query.filter(
            ((Connection.requester_id == self.user_id) & (Connection.requested_id == user.user_id)) |
            ((Connection.requester_id == user.user_id) & (Connection.requested_id == self.user_id))
        ).first()
        return connection.status if connection else None

class Post(db.Model):
    __tablename__ = 'posts'

    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.Enum('text', 'image', 'video', 'link', 'document', name='post_type_enum'), default='text')
    media_url = db.Column(db.String(1000))
    link_url = db.Column(db.String(1000))
    link_title = db.Column(db.String(500))
    link_description = db.Column(db.Text)
    link_image_url = db.Column(db.String(1000))
    visibility = db.Column(db.Enum('public', 'connections', 'private', name='visibility_enum'), default='public')
    allow_comments = db.Column(db.Boolean, default=True)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reactions = relationship('PostReaction', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    shares = relationship('PostShare', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def get_reaction_count(self, reaction_type=None):
        if reaction_type:
            return self.reactions.filter_by(reaction_type=reaction_type).count()
        return self.reactions.count()

    def get_comment_count(self):
        return self.comments.count()

    def get_share_count(self):
        return self.shares.count()

class PostReaction(db.Model):
    __tablename__ = 'post_reactions'

    reaction_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    reaction_type = db.Column(db.Enum('like', 'love', 'celebrate', 'support', 'funny', 'insightful', name='reaction_enum'), default='like')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_reaction'),)

class Comment(db.Model):
    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referencing relationship for replies
    replies = relationship('Comment', backref=db.backref('parent', remote_side=[comment_id]), lazy='dynamic')
    reactions = relationship('CommentReaction', backref='comment', lazy='dynamic', cascade='all, delete-orphan')
    author = relationship('User', backref='comments')

class CommentReaction(db.Model):
    __tablename__ = 'comment_reactions'

    reaction_id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    reaction_type = db.Column(db.Enum('like', 'love', 'celebrate', 'support', 'funny', 'insightful', name='comment_reaction_enum'), default='like')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_reaction'),)

class PostShare(db.Model):
    __tablename__ = 'post_shares'

    share_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    share_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = relationship('User', backref='shared_posts')

class Connection(db.Model):
    __tablename__ = 'connections'

    connection_id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    requested_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'blocked', name='connection_status_enum'), default='pending')
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('requester_id', 'requested_id', name='unique_connection'),)

class Skill(db.Model):
    __tablename__ = 'skills'

    skill_id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    __tablename__ = 'companies'

    company_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False, index=True)
    company_website = db.Column(db.String(500))
    company_logo_url = db.Column(db.String(500))
    company_size = db.Column(db.Enum('1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001-10000', '10000+', name='company_size_enum'))
    industry = db.Column(db.String(100), index=True)
    headquarters = db.Column(db.String(200))
    founded_year = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkExperience(db.Model):
    __tablename__ = 'work_experiences'

    experience_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'))
    company_name = db.Column(db.String(200))
    job_title = db.Column(db.String(200), nullable=False)
    employment_type = db.Column(db.Enum('Full-time', 'Part-time', 'Self-employed', 'Freelance', 'Contract', 'Internship', name='employment_type_enum'), default='Full-time')
    location = db.Column(db.String(200))
    location_type = db.Column(db.Enum('On-site', 'Remote', 'Hybrid', name='location_type_enum'), default='On-site')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship('Company', backref='employees')

class EducationalInstitution(db.Model):
    __tablename__ = 'educational_institutions'

    institution_id = db.Column(db.Integer, primary_key=True)
    institution_name = db.Column(db.String(200), nullable=False, index=True)
    institution_type = db.Column(db.Enum('University', 'College', 'School', 'Online', 'Other', name='institution_type_enum'), default='University')
    location = db.Column(db.String(200))
    website = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Education(db.Model):
    __tablename__ = 'education'

    education_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('educational_institutions.institution_id'))
    institution_name = db.Column(db.String(200))
    degree_type = db.Column(db.Enum('High School', 'Associate', 'Bachelor', 'Master', 'Doctorate', 'Certificate', 'Other', name='degree_type_enum'))
    field_of_study = db.Column(db.String(200))
    grade = db.Column(db.String(10))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship('EducationalInstitution', backref='students')

class Conversation(db.Model):
    __tablename__ = 'conversations'

    conversation_id = db.Column(db.Integer, primary_key=True)
    conversation_type = db.Column(db.Enum('private', 'group', name='conversation_type_enum'), default='private')
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    creator = relationship('User', foreign_keys=[created_by])

class Message(db.Model):
    __tablename__ = 'messages'

    message_id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    message_type = db.Column(db.Enum('text', 'image', 'video', 'file', 'voice', 'system', name='message_type_enum'), default='text')
    content = db.Column(db.Text)
    media_url = db.Column(db.String(1000))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    reply_to_message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'))
    is_edited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    type = db.Column(db.Enum('connection_request', 'connection_accepted', 'post_like', 'post_comment', 'post_share', 'skill_endorsement', 'message', 'profile_view', 'job_alert', 'system', name='notification_type_enum'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    related_post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'))
    action_url = db.Column(db.String(1000))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = relationship('User', foreign_keys=[user_id], backref='notifications')
    related_user = relationship('User', foreign_keys=[related_user_id])
    related_post = relationship('Post', foreign_keys=[related_post_id])
