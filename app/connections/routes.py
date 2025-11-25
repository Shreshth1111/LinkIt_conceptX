from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.connections import bp
from app.models import User, Connection, Notification
from app.forms import ConnectionRequestForm
from sqlalchemy import or_, and_, func
from datetime import datetime

@bp.route('/my_network')
@login_required
def my_network():
    """Show user's connections and connection requests"""
    # Get accepted connections
    connections_query = db.session.query(User).join(
        Connection, 
        or_(
            and_(Connection.requester_id == current_user.user_id, Connection.requested_id == User.user_id),
            and_(Connection.requested_id == current_user.user_id, Connection.requester_id == User.user_id)
        )
    ).filter(Connection.status == 'accepted')

    connections = connections_query.all()

    # Get pending requests received
    pending_requests = db.session.query(User, Connection).join(
        Connection, Connection.requester_id == User.user_id
    ).filter(
        and_(
            Connection.requested_id == current_user.user_id,
            Connection.status == 'pending'
        )
    ).all()

    # Get pending requests sent
    sent_requests = db.session.query(User, Connection).join(
        Connection, Connection.requested_id == User.user_id
    ).filter(
        and_(
            Connection.requester_id == current_user.user_id,
            Connection.status == 'pending'
        )
    ).all()

    return render_template('connections/my_network.html', title='My Network',
                         connections=connections, pending_requests=pending_requests,
                         sent_requests=sent_requests)

@bp.route('/people')
@login_required
def discover_people():
    """Discover new people to connect with"""
    page = request.args.get('page', 1, type=int)

    # Get users not already connected with
    connected_user_ids = db.session.query(
        Connection.requester_id, Connection.requested_id
    ).filter(
        or_(
            Connection.requester_id == current_user.user_id,
            Connection.requested_id == current_user.user_id
        )
    ).all()

    # Flatten the list of connected user IDs
    excluded_ids = set()
    for req_id, resp_id in connected_user_ids:
        excluded_ids.add(req_id)
        excluded_ids.add(resp_id)

    # Add current user to exclusion list
    excluded_ids.add(current_user.user_id)

    # Get suggested users
    suggested_users = User.query.filter(
        ~User.user_id.in_(excluded_ids)
    ).paginate(page=page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)

    return render_template('connections/discover_people.html', title='People You May Know',
                         users=suggested_users)

@bp.route('/send_request/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_connection_request(user_id):
    """Send a connection request to another user"""
    if user_id == current_user.user_id:
        flash('You cannot send a connection request to yourself.', 'error')
        return redirect(url_for('connections.discover_people'))

    target_user = User.query.get_or_404(user_id)

    # Check if connection already exists
    existing_connection = Connection.query.filter(
        or_(
            and_(Connection.requester_id == current_user.user_id, Connection.requested_id == user_id),
            and_(Connection.requester_id == user_id, Connection.requested_id == current_user.user_id)
        )
    ).first()

    if existing_connection:
        if existing_connection.status == 'accepted':
            flash('You are already connected with this user.', 'info')
        elif existing_connection.status == 'pending':
            flash('Connection request already sent.', 'info')
        elif existing_connection.status == 'blocked':
            flash('Cannot send connection request to this user.', 'error')
        return redirect(url_for('profile.view_profile', username=target_user.username))

    form = ConnectionRequestForm()
    if form.validate_on_submit():
        connection = Connection(
            requester_id=current_user.user_id,
            requested_id=user_id,
            message=form.message.data,
            status='pending'
        )
        db.session.add(connection)

        # Create notification for target user
        notification = Notification(
            user_id=user_id,
            type='connection_request',
            title=f'{current_user.get_full_name()} sent you a connection request',
            message=f'{current_user.get_full_name()} would like to connect with you.',
            related_user_id=current_user.user_id,
            action_url=url_for('connections.my_network')
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'Connection request sent to {target_user.get_full_name()}!', 'success')
        return redirect(url_for('profile.view_profile', username=target_user.username))

    return render_template('connections/send_request.html', title='Send Connection Request',
                         form=form, user=target_user)

@bp.route('/respond_request/<int:connection_id>/<action>')
@login_required
def respond_to_request(connection_id, action):
    """Accept or reject a connection request"""
    connection = Connection.query.get_or_404(connection_id)

    # Verify this request is for current user
    if connection.requested_id != current_user.user_id:
        flash('Invalid connection request.', 'error')
        return redirect(url_for('connections.my_network'))

    if connection.status != 'pending':
        flash('This connection request has already been processed.', 'info')
        return redirect(url_for('connections.my_network'))

    if action == 'accept':
        connection.status = 'accepted'
        connection.updated_at = datetime.utcnow()

        # Create notification for requester
        notification = Notification(
            user_id=connection.requester_id,
            type='connection_accepted',
            title=f'{current_user.get_full_name()} accepted your connection request',
            message=f'You are now connected with {current_user.get_full_name()}.',
            related_user_id=current_user.user_id,
            action_url=url_for('profile.view_profile', username=current_user.username)
        )
        db.session.add(notification)

        flash(f'You are now connected with {connection.requester.get_full_name()}!', 'success')

    elif action == 'reject':
        connection.status = 'rejected'
        connection.updated_at = datetime.utcnow()
        flash('Connection request rejected.', 'info')

    else:
        flash('Invalid action.', 'error')
        return redirect(url_for('connections.my_network'))

    db.session.commit()
    return redirect(url_for('connections.my_network'))

@bp.route('/remove_connection/<int:user_id>', methods=['POST'])
@login_required
def remove_connection(user_id):
    """Remove a connection"""
    connection = Connection.query.filter(
        or_(
            and_(Connection.requester_id == current_user.user_id, Connection.requested_id == user_id),
            and_(Connection.requester_id == user_id, Connection.requested_id == current_user.user_id)
        )
    ).filter(Connection.status == 'accepted').first()

    if not connection:
        return jsonify({'status': 'error', 'message': 'Connection not found'})

    user = User.query.get(user_id)
    db.session.delete(connection)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Connection with {user.get_full_name() if user else "user"} removed'
    })

@bp.route('/cancel_request/<int:connection_id>', methods=['POST'])
@login_required
def cancel_request(connection_id):
    """Cancel a sent connection request"""
    connection = Connection.query.get_or_404(connection_id)

    if connection.requester_id != current_user.user_id or connection.status != 'pending':
        return jsonify({'status': 'error', 'message': 'Cannot cancel this request'})

    db.session.delete(connection)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Connection request cancelled'})

@bp.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    """Block a user"""
    if user_id == current_user.user_id:
        return jsonify({'status': 'error', 'message': 'Cannot block yourself'})

    # Remove any existing connection
    existing_connection = Connection.query.filter(
        or_(
            and_(Connection.requester_id == current_user.user_id, Connection.requested_id == user_id),
            and_(Connection.requester_id == user_id, Connection.requested_id == current_user.user_id)
        )
    ).first()

    if existing_connection:
        existing_connection.status = 'blocked'
        existing_connection.updated_at = datetime.utcnow()
    else:
        # Create new blocked connection
        connection = Connection(
            requester_id=current_user.user_id,
            requested_id=user_id,
            status='blocked'
        )
        db.session.add(connection)

    db.session.commit()

    user = User.query.get(user_id)
    return jsonify({
        'status': 'success',
        'message': f'User {user.get_full_name() if user else "user"} has been blocked'
    })
