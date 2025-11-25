from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.models import User, Notification
from app.forms import LoginForm, RegistrationForm
from datetime import datetime
import os

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password', 'danger')
            return redirect(url_for('auth.login'))

        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=form.remember_me.data)

        # Redirect to next page or home
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')

        flash(f'Welcome back, {user.first_name}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            first_name=form.first_name.data,
            middle_name=form.middle_name.data if form.middle_name.data else None,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Create welcome notification
        welcome_notification = Notification(
            user_id=user.user_id,
            type='system',
            title='Welcome to LinkedIn Clone!',
            message='Thank you for joining our professional network. Complete your profile to get started.',
            action_url=url_for('profile.edit_profile')
        )
        db.session.add(welcome_notification)
        db.session.commit()

        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/forgot_password')
def forgot_password():
    # TODO: Implement password reset functionality
    flash('Password reset functionality will be available soon.', 'info')
    return redirect(url_for('auth.login'))
