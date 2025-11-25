from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.messages import bp
from app.models import User, Conversation, Message, Notification
from app.forms import MessageForm
from sqlalchemy import or_, and_, desc
from datetime import datetime
import os
import uuid

@bp.route('/inbox')
@login_required
def inbox():
    """Show user's message inbox"""
    # Get conversations where user is a participant
    conversations = db.session.query(Conversation).join(
        Conversation.participants
    ).filter(User.user_id == current_user.user_id).order_by(
        desc(Conversation.updated_at)
    ).all()

    # Get latest message for each conversation
    conversation_data = []
    for conv in conversations:
        latest_message = Message.query.filter_by(
            conversation_id=conv.conversation_id
        ).order_by(desc(Message.created_at)).first()

        # Get other participants (exclude current user)
        other_participants = [p for p in conv.participants if p.user_id != current_user.user_id]

        conversation_data.append({
            'conversation': conv,
            'latest_message': latest_message,
            'other_participants': other_participants,
            'unread_count': Message.query.filter_by(
                conversation_id=conv.conversation_id
            ).filter(Message.sender_id != current_user.user_id).count()  # Simplified unread logic
        })

    return render_template('messages/inbox.html', title='Messages', 
                         conversation_data=conversation_data)

@bp.route('/conversation/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    """View a specific conversation"""
    conversation = Conversation.query.get_or_404(conversation_id)

    # Check if user is participant
    if current_user not in conversation.participants:
        flash('You do not have access to this conversation.', 'error')
        return redirect(url_for('messages.inbox'))

    # Get messages
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.created_at.asc()).paginate(
        page=page, per_page=current_app.config['MESSAGES_PER_PAGE'], error_out=False
    )

    # Get other participants
    other_participants = [p for p in conversation.participants if p.user_id != current_user.user_id]

    form = MessageForm()

    return render_template('messages/conversation.html', title='Conversation',
                         conversation=conversation, messages=messages,
                         other_participants=other_participants, form=form)

@bp.route('/new_message/<username>')
@login_required
def new_message(username):
    """Start a new conversation with a user"""
    recipient = User.query.filter_by(username=username).first_or_404()

    if recipient.user_id == current_user.user_id:
        flash('You cannot send a message to yourself.', 'error')
        return redirect(url_for('messages.inbox'))

    # Check if conversation already exists
    existing_conversation = db.session.query(Conversation).join(
        Conversation.participants
    ).filter(User.user_id == current_user.user_id).join(
        Conversation.participants.and_(User.user_id == recipient.user_id)
    ).filter(Conversation.conversation_type == 'private').first()

    if existing_conversation:
        return redirect(url_for('messages.view_conversation', 
                              conversation_id=existing_conversation.conversation_id))

    form = MessageForm()
    form.recipient_id.data = recipient.user_id

    return render_template('messages/new_message.html', title='New Message',
                         recipient=recipient, form=form)

@bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Send a message"""
    form = MessageForm()
    if form.validate_on_submit():
        recipient_id = form.recipient_id.data
        recipient = User.query.get_or_404(recipient_id)

        # Find or create conversation
        conversation = db.session.query(Conversation).join(
            Conversation.participants
        ).filter(User.user_id == current_user.user_id).join(
            Conversation.participants.and_(User.user_id == recipient_id)
        ).filter(Conversation.conversation_type == 'private').first()

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                conversation_type='private',
                created_by=current_user.user_id
            )
            conversation.participants.append(current_user)
            conversation.participants.append(recipient)
            db.session.add(conversation)
            db.session.flush()  # Get the ID

        # Create message
        message = Message(
            conversation_id=conversation.conversation_id,
            sender_id=current_user.user_id,
            content=form.content.data,
            message_type=form.message_type.data
        )

        # Handle media upload
        if form.media_file.data:
            file = form.media_file.data
            if file.filename:
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename

                # Determine upload folder
                file_ext = filename.rsplit('.', 1)[1].lower()
                if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'messages', 'images')
                    message.message_type = 'image'
                else:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'messages', 'files')
                    message.message_type = 'file'

                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)

                message.media_url = f'uploads/messages/{message.message_type}s/{unique_filename}'
                message.file_name = filename
                message.file_size = os.path.getsize(file_path)

        db.session.add(message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        # Create notification for recipient
        notification = Notification(
            user_id=recipient_id,
            type='message',
            title=f'New message from {current_user.get_full_name()}',
            message=f'{current_user.get_full_name()}: {form.content.data[:50]}...',
            related_user_id=current_user.user_id,
            action_url=url_for('messages.view_conversation', 
                              conversation_id=conversation.conversation_id)
        )
        db.session.add(notification)

        db.session.commit()

        flash('Message sent!', 'success')
        return redirect(url_for('messages.view_conversation', 
                              conversation_id=conversation.conversation_id))

    # If form validation fails, redirect back
    flash('Error sending message. Please try again.', 'error')
    return redirect(url_for('messages.inbox'))

@bp.route('/api/send_quick_message', methods=['POST'])
@login_required
def send_quick_message():
    """API endpoint for sending messages via AJAX"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    content = data.get('content')

    if not conversation_id or not content:
        return jsonify({'status': 'error', 'message': 'Missing required data'})

    conversation = Conversation.query.get_or_404(conversation_id)

    # Check if user is participant
    if current_user not in conversation.participants:
        return jsonify({'status': 'error', 'message': 'Access denied'})

    # Create message
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.user_id,
        content=content,
        message_type='text'
    )
    db.session.add(message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    # Create notifications for other participants
    for participant in conversation.participants:
        if participant.user_id != current_user.user_id:
            notification = Notification(
                user_id=participant.user_id,
                type='message',
                title=f'New message from {current_user.get_full_name()}',
                message=f'{current_user.get_full_name()}: {content[:50]}...',
                related_user_id=current_user.user_id,
                action_url=url_for('messages.view_conversation', 
                                  conversation_id=conversation_id)
            )
            db.session.add(notification)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': {
            'id': message.message_id,
            'content': message.content,
            'sender_name': current_user.get_full_name(),
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@bp.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    message = Message.query.get_or_404(message_id)

    if message.sender_id != current_user.user_id:
        return jsonify({'status': 'error', 'message': 'You can only delete your own messages'})

    # Delete associated media file
    if message.media_url:
        file_path = os.path.join(current_app.root_path, 'static', message.media_url)
        if os.path.exists(file_path):
            os.remove(file_path)

    conversation_id = message.conversation_id
    db.session.delete(message)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Message deleted'})

@bp.route('/search_users')
@login_required
def search_users():
    """Search users for messaging"""
    query = request.args.get('q', '', type=str)

    if len(query) < 2:
        return jsonify([])

    users = User.query.filter(
        and_(
            User.user_id != current_user.user_id,
            or_(
                User.first_name.contains(query),
                User.last_name.contains(query),
                User.username.contains(query)
            )
        )
    ).limit(10).all()

    user_list = []
    for user in users:
        user_list.append({
            'user_id': user.user_id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'profile_picture': user.profile_picture_url or '/static/img/default-avatar.png'
        })

    return jsonify(user_list)
