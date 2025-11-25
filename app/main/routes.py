from flask import render_template, request, current_app, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.models import User, Post, Connection, Notification, PostReaction, Comment
from app.forms import SearchForm
from sqlalchemy import or_, and_, desc
from datetime import datetime, timedelta

@bp.route('/')
@bp.route('/index')
def index():
    # If user is not logged in, show landing page
    if not current_user.is_authenticated:
        return render_template('main/landing.html', title='Welcome to LinkedIn Clone')

    # Get posts from user's connections and own posts
    page = request.args.get('page', 1, type=int)

    # Get connected user IDs
    connected_users = db.session.query(Connection.requester_id, Connection.requested_id).filter(
        and_(
            or_(Connection.requester_id == current_user.user_id, Connection.requested_id == current_user.user_id),
            Connection.status == 'accepted'
        )
    ).all()

    connected_user_ids = set()
    for req_id, resp_id in connected_users:
        if req_id == current_user.user_id:
            connected_user_ids.add(resp_id)
        else:
            connected_user_ids.add(req_id)

    # Add current user's own posts
    connected_user_ids.add(current_user.user_id)

    # Get posts from connections and public posts
    posts = Post.query.filter(
        or_(
            Post.user_id.in_(connected_user_ids),
            Post.visibility == 'public'
        )
    ).order_by(desc(Post.created_at)).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )

    # Get connection suggestions (users not already connected)
    suggestions = User.query.filter(
        and_(
            User.user_id != current_user.user_id,
            ~User.user_id.in_(connected_user_ids)
        )
    ).limit(5).all()

    # Get unread notifications count
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).count()

    return render_template('main/index.html', title='Home', posts=posts, 
                         suggestions=suggestions, unread_notifications=unread_notifications)

@bp.route('/explore')
@login_required
def explore():
    """Explore page showing all public posts"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(visibility='public').order_by(desc(Post.created_at)).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )
    return render_template('main/explore.html', title='Explore', posts=posts)

@bp.route('/search')
@login_required
def search():
    form = SearchForm()
    results = {'users': [], 'posts': [], 'companies': []}
    query = request.args.get('q', '', type=str)
    search_type = request.args.get('type', 'all', type=str)

    if query:
        if search_type in ['all', 'people']:
            # Search users
            users = User.query.filter(
                or_(
                    User.first_name.contains(query),
                    User.last_name.contains(query),
                    User.username.contains(query),
                    User.headline.contains(query)
                )
            ).limit(20).all()
            results['users'] = users

        if search_type in ['all', 'posts']:
            # Search posts
            posts = Post.query.filter(
                and_(
                    Post.content.contains(query),
                    or_(
                        Post.visibility == 'public',
                        Post.user_id == current_user.user_id
                    )
                )
            ).order_by(desc(Post.created_at)).limit(20).all()
            results['posts'] = posts

    return render_template('main/search.html', title='Search Results', 
                         form=form, results=results, query=query, search_type=search_type)

@bp.route('/about')
def about():
    return render_template('main/about.html', title='About')

@bp.route('/api/react_post/<int:post_id>', methods=['POST'])
@login_required
def react_to_post(post_id):
    """API endpoint to react to a post"""
    post = Post.query.get_or_404(post_id)
    reaction_type = request.json.get('reaction_type', 'like')

    # Check if user already reacted
    existing_reaction = PostReaction.query.filter_by(
        post_id=post_id, user_id=current_user.user_id
    ).first()

    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            # Remove reaction
            db.session.delete(existing_reaction)
            action = 'removed'
        else:
            # Update reaction type
            existing_reaction.reaction_type = reaction_type
            action = 'updated'
    else:
        # Add new reaction
        new_reaction = PostReaction(
            post_id=post_id,
            user_id=current_user.user_id,
            reaction_type=reaction_type
        )
        db.session.add(new_reaction)
        action = 'added'

        # Create notification for post author (if not self)
        if post.user_id != current_user.user_id:
            notification = Notification(
                user_id=post.user_id,
                type='post_like',
                title=f'{current_user.get_full_name()} reacted to your post',
                message=f'{current_user.get_full_name()} {reaction_type}d your post.',
                related_user_id=current_user.user_id,
                related_post_id=post_id,
                action_url=url_for('posts.view_post', id=post_id)
            )
            db.session.add(notification)

    db.session.commit()

    # Return updated counts
    return jsonify({
        'status': 'success',
        'action': action,
        'reaction_count': post.get_reaction_count(),
        'like_count': post.get_reaction_count('like'),
        'love_count': post.get_reaction_count('love'),
        'celebrate_count': post.get_reaction_count('celebrate'),
        'support_count': post.get_reaction_count('support'),
        'funny_count': post.get_reaction_count('funny'),
        'insightful_count': post.get_reaction_count('insightful')
    })

@bp.route('/notifications')
@login_required
def notifications():
    """Show user notifications"""
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(
        desc(Notification.created_at)
    ).paginate(page=page, per_page=20, error_out=False)

    # Mark all as read
    Notification.query.filter_by(user_id=current_user.user_id, is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('main/notifications.html', title='Notifications', notifications=notifications)

@bp.route('/api/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.filter_by(
        notification_id=notification_id, user_id=current_user.user_id
    ).first_or_404()

    notification.is_read = True
    db.session.commit()

    return jsonify({'status': 'success'})
