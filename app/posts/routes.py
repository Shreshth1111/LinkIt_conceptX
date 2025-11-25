from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.posts import bp
from app.models import Post, PostReaction, Comment, PostShare, User, Notification
from app.forms import PostForm, CommentForm
from datetime import datetime
import os
import uuid

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            user_id=current_user.user_id,
            content=form.content.data,
            post_type=form.post_type.data,
            visibility=form.visibility.data,
            allow_comments=form.allow_comments.data
        )

        # Handle media upload
        if form.media_file.data:
            file = form.media_file.data
            if allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename

                # Determine upload folder based on file type
                file_ext = filename.rsplit('.', 1)[1].lower()
                if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', 'images')
                    post.post_type = 'image'
                elif file_ext in ['mp4', 'avi', 'mov']:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', 'videos')
                    post.post_type = 'video'
                else:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', 'documents')
                    post.post_type = 'document'

                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)

                # Store relative path
                post.media_url = f'uploads/posts/{post.post_type}s/{unique_filename}'

        # Handle link data
        if form.post_type.data == 'link' and form.link_url.data:
            post.link_url = form.link_url.data
            post.link_title = form.link_title.data
            post.link_description = form.link_description.data

        db.session.add(post)
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('main.index'))

    return render_template('posts/create_post.html', title='Create Post', form=form)

@bp.route('/post/<int:id>')
def view_post(id):
    post = Post.query.get_or_404(id)

    # Check visibility permissions
    if post.visibility == 'private' and post.user_id != current_user.user_id:
        flash('This post is private.', 'error')
        return redirect(url_for('main.index'))

    if post.visibility == 'connections' and not current_user.is_connected_with(post.author):
        flash('This post is only visible to connections.', 'error')
        return redirect(url_for('main.index'))

    # Get comments
    comments = Comment.query.filter_by(post_id=id, parent_comment_id=None).order_by(Comment.created_at.asc()).all()

    comment_form = CommentForm()

    return render_template('posts/view_post.html', title='Post', post=post, 
                         comments=comments, comment_form=comment_form)

@bp.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    if post.user_id != current_user.user_id:
        flash('You can only edit your own posts.', 'error')
        return redirect(url_for('posts.view_post', id=id))

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.content = form.content.data
        post.visibility = form.visibility.data
        post.allow_comments = form.allow_comments.data
        post.updated_at = datetime.utcnow()

        # Handle new media upload if provided
        if form.media_file.data:
            file = form.media_file.data
            if allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                # Delete old media file if exists
                if post.media_url:
                    old_file_path = os.path.join(current_app.root_path, 'static', post.media_url)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # Save new file
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename

                file_ext = filename.rsplit('.', 1)[1].lower()
                if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', 'images')
                    post.post_type = 'image'
                else:
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', 'documents')
                    post.post_type = 'document'

                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)

                post.media_url = f'uploads/posts/{post.post_type}s/{unique_filename}'

        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.view_post', id=id))

    return render_template('posts/edit_post.html', title='Edit Post', form=form, post=post)

@bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)

    if post.user_id != current_user.user_id:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('posts.view_post', id=id))

    # Delete associated media file
    if post.media_url:
        file_path = os.path.join(current_app.root_path, 'static', post.media_url)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(post)
    db.session.commit()

    flash('Your post has been deleted.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = Post.query.get_or_404(id)

    if not post.allow_comments:
        flash('Comments are not allowed on this post.', 'error')
        return redirect(url_for('posts.view_post', id=id))

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            post_id=id,
            user_id=current_user.user_id,
            content=form.content.data
        )
        db.session.add(comment)

        # Create notification for post author (if not self)
        if post.user_id != current_user.user_id:
            notification = Notification(
                user_id=post.user_id,
                type='post_comment',
                title=f'{current_user.get_full_name()} commented on your post',
                message=f'{current_user.get_full_name()} commented: "{form.content.data[:50]}..."',
                related_user_id=current_user.user_id,
                related_post_id=id,
                action_url=url_for('posts.view_post', id=id)
            )
            db.session.add(notification)

        db.session.commit()
        flash('Your comment has been added!', 'success')

    return redirect(url_for('posts.view_post', id=id))

@bp.route('/post/<int:id>/share', methods=['POST'])
@login_required
def share_post(id):
    post = Post.query.get_or_404(id)
    share_message = request.json.get('message', '')

    # Check if already shared
    existing_share = PostShare.query.filter_by(post_id=id, user_id=current_user.user_id).first()
    if existing_share:
        return jsonify({'status': 'error', 'message': 'You have already shared this post'})

    share = PostShare(
        post_id=id,
        user_id=current_user.user_id,
        share_message=share_message
    )
    db.session.add(share)

    # Create notification for post author (if not self)
    if post.user_id != current_user.user_id:
        notification = Notification(
            user_id=post.user_id,
            type='post_share',
            title=f'{current_user.get_full_name()} shared your post',
            message=f'{current_user.get_full_name()} shared your post with their network.',
            related_user_id=current_user.user_id,
            related_post_id=id,
            action_url=url_for('posts.view_post', id=id)
        )
        db.session.add(notification)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Post shared successfully!',
        'share_count': post.get_share_count()
    })

@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)

    if comment.user_id != current_user.user_id:
        return jsonify({'status': 'error', 'message': 'You can only delete your own comments'})

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Comment deleted successfully'})
