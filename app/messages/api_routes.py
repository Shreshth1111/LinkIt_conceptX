# Place this code as app/messages/api_routes.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Message, Conversation
from datetime import datetime

api_bp = Blueprint('messages_api', __name__)

@api_bp.route('/get_messages/<int:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    msg_list = []
    for m in messages:
        msg_list.append({
            'id': m.message_id,
            'sender_id': m.sender_id,
            'sender_name': m.sender.get_full_name(),
            'avatar': m.sender.profile_picture_url,
            'content': m.content,
            'created': m.created_at.strftime('%m/%d %I:%M %p'),
            'self': (m.sender_id==current_user.user_id)
        })
    return jsonify({'messages': msg_list})

@api_bp.route('/edit_message', methods=['POST'])
@login_required
def edit_message():
    data = request.get_json()
    message = Message.query.get_or_404(data['message_id'])
    if message.sender_id != current_user.user_id:
        return jsonify({'status': 'error', 'message': 'Not allowed'})
    message.content = data['content']
    db.session.commit()
    return jsonify({'status': 'success'})
