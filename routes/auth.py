from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.password_reset import PasswordReset
from models.registration_otp import RegistrationOTP
from utils.email_utils import send_otp_email, send_registration_otp
from werkzeug.security import generate_password_hash
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard.admin' if user.is_admin else 'dashboard.user'))
        flash('Invalid credentials')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check for existing username or email
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('auth/register.html')
        
        # Clear any existing OTP for this email
        RegistrationOTP.query.filter_by(email=email).delete()
        
        # Create OTP record
        password_hash = generate_password_hash(password)
        otp_record = RegistrationOTP(email, username, password_hash)
        db.session.add(otp_record)
        db.session.commit()
        
        try:
            send_registration_otp(email, otp_record.otp_code)
            flash('OTP sent to your email. Please verify to complete registration.')
            return redirect(url_for('auth.verify_registration', email=email))
        except Exception as e:
            flash('Failed to send verification email. Please try again.')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Invalidate existing OTPs
            PasswordReset.query.filter_by(user_id=user.id, is_used=False).update({'is_used': True})
            
            # Create new OTP
            reset_request = PasswordReset(user.id)
            db.session.add(reset_request)
            db.session.commit()
            
            try:
                send_otp_email(user.email, reset_request.otp_code)
                flash('OTP sent to your email')
                return redirect(url_for('auth.verify_otp', email=email))
            except Exception as e:
                flash('Failed to send email. Please try again.')
        else:
            flash('Email not found')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email') or request.form.get('email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_request = PasswordReset.query.filter_by(
                user_id=user.id, otp_code=otp, is_used=False
            ).first()
            
            if reset_request and reset_request.is_valid():
                return redirect(url_for('auth.reset_password', token=reset_request.otp_code, email=email))
            else:
                flash('Invalid or expired OTP')
        else:
            flash('Invalid request')
    
    return render_template('auth/verify_otp.html', email=email)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') or request.form.get('token')
    email = request.args.get('email') or request.form.get('email')
    
    if not token or not email:
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect(url_for('auth.forgot_password'))
    
    # Ensure OTP belongs to the specific user requesting password reset
    reset_request = PasswordReset.query.filter_by(
        user_id=user.id, otp_code=token, is_used=False
    ).first()
    
    if not reset_request or not reset_request.belongs_to_user(user.id):
        flash('Invalid or expired token')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/reset_password.html', token=token, email=email)
        
        # Security: Verify OTP belongs to user before password update
        if reset_request.belongs_to_user(user.id):
            user.set_password(password)
            reset_request.mark_used()
            db.session.commit()
            flash('Password updated successfully')
        else:
            flash('Security error: Invalid request')
            return redirect(url_for('auth.forgot_password'))
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token, email=email)

@auth_bp.route('/profile-reset-password', methods=['POST'])
@login_required
def profile_reset_password():
    # Invalidate existing OTPs
    PasswordReset.query.filter_by(user_id=current_user.id, is_used=False).update({'is_used': True})
    
    # Create new OTP
    reset_request = PasswordReset(current_user.id)
    db.session.add(reset_request)
    db.session.commit()
    
    try:
        send_otp_email(current_user.email, reset_request.otp_code)
        return jsonify({'success': True, 'message': 'OTP sent to your email'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to send email'})

@auth_bp.route('/profile-verify-otp', methods=['POST'])
@login_required
def profile_verify_otp():
    otp = request.json.get('otp')
    new_password = request.json.get('password')
    
    # Ensure OTP belongs to the currently logged-in user only
    reset_request = PasswordReset.query.filter_by(
        user_id=current_user.id, otp_code=otp, is_used=False
    ).first()
    
    if reset_request and reset_request.belongs_to_user(current_user.id):
        # Security: Verify OTP belongs to authenticated user
        current_user.set_password(new_password)
        reset_request.mark_used()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'})

@auth_bp.route('/verify-registration', methods=['GET', 'POST'])
def verify_registration():
    email = request.args.get('email') or request.form.get('email')
    if not email:
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        otp_record = RegistrationOTP.query.filter_by(
            email=email, otp_code=otp, is_used=False
        ).first()
        
        if otp_record and otp_record.is_valid():
            # Create user account
            user = User(
                username=otp_record.username,
                email=otp_record.email
            )
            user.password_hash = otp_record.password_hash
            
            db.session.add(user)
            otp_record.mark_used()
            db.session.commit()
            
            login_user(user)
            flash('Registration successful! Welcome to TimeGuard.')
            return redirect(url_for('dashboard.user'))
        else:
            flash('Invalid or expired OTP')
    
    return render_template('auth/verify_registration.html', email=email)

@auth_bp.route('/resend-registration-otp', methods=['POST'])
def resend_registration_otp():
    email = request.form.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email required'})
    
    otp_record = RegistrationOTP.query.filter_by(email=email, is_used=False).first()
    if not otp_record:
        return jsonify({'success': False, 'message': 'No pending registration found'})
    
    # Generate new OTP
    otp_record.otp_code = ''.join(random.choices(string.digits, k=6))
    otp_record.expires_at = now_ist().replace(tzinfo=None) + timedelta(minutes=10)
    db.session.commit()
    
    try:
        send_registration_otp(email, otp_record.otp_code)
        return jsonify({'success': True, 'message': 'New OTP sent to your email'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to send OTP'})

import random
import string
from datetime import datetime, timedelta
from utils.timezone_utils import now_ist