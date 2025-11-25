from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.profile import bp
from app.models import User, Post, WorkExperience, Education, Skill, Connection, Notification
from app.forms import ProfileForm, WorkExperienceForm, EducationForm
from sqlalchemy import or_, and_, desc, func
from datetime import datetime
import os
import uuid

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file, folder_name):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return f'uploads/{folder_name}/{unique_filename}'
    return None

@bp.route('/<username>')
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    if user.privacy_level == 'Private' and (not current_user.is_authenticated or current_user.user_id != user.user_id):
        flash('This profile is private.', 'info')
        return redirect(url_for('main.index'))

    if user.privacy_level == 'Connections Only' and current_user.is_authenticated:
        if current_user.user_id != user.user_id and not current_user.is_connected_with(user):
            flash('This profile is only visible to connections.', 'info')
            return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts_query = Post.query.filter_by(user_id=user.user_id)

    if not current_user.is_authenticated or current_user.user_id != user.user_id:
        posts_query = posts_query.filter(or_(Post.visibility == 'public', and_(Post.visibility == 'connections', current_user.is_authenticated, current_user.is_connected_with(user))))

    posts = posts_query.order_by(desc(Post.created_at)).paginate(page=page, per_page=10, error_out=False)

    work_experiences = WorkExperience.query.filter_by(user_id=user.user_id).order_by(desc(WorkExperience.start_date)).all()
    education = Education.query.filter_by(user_id=user.user_id).order_by(desc(Education.start_date)).all()
    skills = user.skills

    connection_status = None
    connection_id = None
    if current_user.is_authenticated and current_user.user_id != user.user_id:
        connection = Connection.query.filter(or_(and_(Connection.requester_id == current_user.user_id, Connection.requested_id == user.user_id), and_(Connection.requester_id == user.user_id, Connection.requested_id == current_user.user_id))).first()
        if connection:
            connection_status = connection.status
            connection_id = connection.connection_id

    connection_count = Connection.query.filter(or_(Connection.requester_id == user.user_id, Connection.requested_id == user.user_id)).filter(Connection.status == 'accepted').count()

    if current_user.is_authenticated and current_user.user_id != user.user_id:
        today = datetime.utcnow().date()
        existing_view_today = Notification.query.filter(and_(Notification.user_id == user.user_id, Notification.related_user_id == current_user.user_id, Notification.type == 'profile_view', func.date(Notification.created_at) == today)).first()
        if not existing_view_today:
            notification = Notification(user_id=user.user_id, type='profile_view', title=f'{current_user.get_full_name()} viewed your profile', message=f'{current_user.get_full_name()} viewed your profile.', related_user_id=current_user.user_id, action_url=url_for('profile.view_profile', username=current_user.username))
            db.session.add(notification)
            db.session.commit()

    return render_template('profile/view_profile.html', title=f'{user.get_full_name()}', user=user, posts=posts, work_experiences=work_experiences, education=education, skills=skills, connection_status=connection_status, connection_id=connection_id, connection_count=connection_count)

@bp.route('/edit')
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    return render_template('profile/edit_profile.html', title='Edit Profile', form=form)

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        try:
            current_user.first_name = form.first_name.data
            current_user.middle_name = form.middle_name.data if form.middle_name.data else None
            current_user.last_name = form.last_name.data
            current_user.headline = form.headline.data
            current_user.summary = form.summary.data
            current_user.location = form.location.data
            current_user.industry = form.industry.data
            current_user.current_position = form.current_position.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.gender = form.gender.data if form.gender.data else None
            current_user.phone_number = form.phone_number.data
            current_user.privacy_level = form.privacy_level.data
            current_user.updated_at = datetime.utcnow()

            if form.profile_picture.data:
                if current_user.profile_picture_url:
                    old_file_path = os.path.join(current_app.root_path, 'static', current_user.profile_picture_url)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass
                profile_pic_path = save_profile_image(form.profile_picture.data, 'profiles')
                if profile_pic_path:
                    current_user.profile_picture_url = profile_pic_path
                else:
                    flash('Invalid profile picture format. Please use JPG, PNG, or GIF.', 'error')
                    return render_template('profile/edit_profile.html', title='Edit Profile', form=form)

            if form.cover_photo.data:
                if current_user.cover_photo_url:
                    old_file_path = os.path.join(current_app.root_path, 'static', current_user.cover_photo_url)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass
                cover_pic_path = save_profile_image(form.cover_photo.data, 'profiles')
                if cover_pic_path:
                    current_user.cover_photo_url = cover_pic_path
                else:
                    flash('Invalid cover photo format. Please use JPG, PNG, or GIF.', 'error')
                    return render_template('profile/edit_profile.html', title='Edit Profile', form=form)

            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('profile.view_profile', username=current_user.username))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating your profile: {str(e)}', 'error')
            return render_template('profile/edit_profile.html', title='Edit Profile', form=form)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    return render_template('profile/edit_profile.html', title='Edit Profile', form=form)
