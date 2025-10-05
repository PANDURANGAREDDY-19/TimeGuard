from utils.timezone_utils import format_ist_datetime

def generate_task_history_text(user, tasks):
    lines = [f"Task History for {user.username}",
             "Title,Status,Priority,Category,Created,Started,Completed,Actual Time (h)"]
    for t in tasks:
        line = f'"{t.title}","{t.status}","{t.priority}","{t.category or ''}","{format_ist_datetime(t.created_at)}","{format_ist_datetime(t.started_at)}","{format_ist_datetime(t.completed_at)}","{t.actual_time or '-'}"'
        lines.append(line)
    return '\n'.join(lines)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

def send_task_history_email(to_email, subject, text_content):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')

    if not smtp_user or not smtp_password:
        print("[EMAIL ERROR] SMTP_USER and SMTP_PASSWORD must be set in config.")
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = to_email

    # Attach plain text part
    part_text = MIMEText(text_content, 'plain')
    msg.attach(part_text)

    # Try to import user and tasks from caller's context for HTML
    user = None
    tasks = None
    import inspect
    frame = inspect.currentframe().f_back
    if 'user' in frame.f_locals:
        user = frame.f_locals['user']
    if 'tasks' in frame.f_locals:
        tasks = frame.f_locals['tasks']
    if user and tasks:
        html_content = generate_task_history_html(user, tasks)
        part_html = MIMEText(html_content, 'html')
        msg.attach(part_html)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Email sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        raise

# --- Weekly Summary Email ---
from datetime import datetime, timedelta
from utils.timezone_utils import now_ist

def generate_weekly_summary(user, tasks):
    completed_tasks = [t for t in tasks if t.status == 'completed' and t.completed_at and t.completed_at >= now_ist().replace(tzinfo=None) - timedelta(days=7)]
    total_time = sum(t.actual_time or 0 for t in completed_tasks)
    task_count = len(completed_tasks)
    # Performance trend: compare to previous week
    prev_week_tasks = [t for t in tasks if t.status == 'completed' and t.completed_at and now_ist().replace(tzinfo=None) - timedelta(days=14) <= t.completed_at < now_ist().replace(tzinfo=None) - timedelta(days=7)]
    prev_total_time = sum(t.actual_time or 0 for t in prev_week_tasks)
    prev_task_count = len(prev_week_tasks)
    trend = 'No change'
    if prev_task_count:
        if task_count > prev_task_count:
            trend = f"↑ {task_count - prev_task_count} more tasks than last week"
        elif task_count < prev_task_count:
            trend = f"↓ {prev_task_count - task_count} fewer tasks than last week"
        else:
            trend = 'Same as last week'
    html = f"""
    <h2>Weekly Summary for {user.username}</h2>
    <p><b>Tasks completed:</b> {task_count}</p>
    <p><b>Total time spent:</b> {round(total_time, 2)} hours</p>
    <p><b>Performance trend:</b> {trend}</p>
    <table border='1' cellpadding='5' cellspacing='0'>
        <tr>
            <th>Title</th><th>Category</th><th>Completed</th><th>Actual Time (h)</th>
        </tr>
"""
    for t in completed_tasks:
        html += f"""
        <tr>
            <td>{t.title}</td>
            <td>{t.category or ''}</td>
            <td>{format_ist_datetime(t.completed_at)}</td>
            <td>{t.actual_time or '-'}</td>
        </tr>
        """
    html += "</table>"
    return html

def send_weekly_summary_email(user, tasks):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    if not smtp_user or not smtp_password:
        print("[EMAIL ERROR] SMTP_USER and SMTP_PASSWORD must be set in config.")
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    subject = f"Your Weekly Task Summary - {user.username}"
    html_content = generate_weekly_summary(user, tasks)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = user.email
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, user.email, msg.as_string())
        print(f"[EMAIL SUCCESS] Weekly summary sent to {user.email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send weekly summary to {user.email}: {e}")
        raise

def generate_task_history_html(user, tasks):
    html = f"""
    <h3>Task History for {user.username}</h3>
    <table border='1' cellpadding='5' cellspacing='0'>
        <tr>
            <th>Title</th><th>Status</th><th>Priority</th><th>Category</th><th>Created</th><th>Started</th><th>Completed</th><th>Actual Time (h)</th>
        </tr>
    """
    for t in tasks:
        html += f"""
        <tr>
            <td>{t.title}</td>
            <td>{t.status}</td>
            <td>{t.priority}</td>
            <td>{t.category or ''}</td>
            <td>{format_ist_datetime(t.created_at)}</td>
            <td>{format_ist_datetime(t.started_at)}</td>
            <td>{format_ist_datetime(t.completed_at)}</td>
            <td>{t.actual_time or '-'}</td>
        </tr>
        """
    html += "</table>"
    return html
def send_otp_email(to_email, otp_code):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    
    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    
    subject = "TimeGuard - Password Reset OTP"
    html_content = f"""
    <h2>Password Reset Request</h2>
    <p>Your OTP for password reset is: <strong>{otp_code}</strong></p>
    <p>This OTP will expire in 10 minutes.</p>
    <p>If you didn't request this, please ignore this email.</p>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = to_email
    
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[EMAIL SUCCESS] OTP sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP to {to_email}: {e}")
        raise
def send_task_assignment_email(to_email, task_title, deadline=None):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    
    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    
    subject = f"TimeGuard - New Task Assigned: {task_title}"
    deadline_text = f"<p><strong>Deadline:</strong> {format_ist_datetime(deadline)}</p>" if deadline else ""
    
    html_content = f"""
    <h2>New Task Assigned</h2>
    <p>You have been assigned a new task: <strong>{task_title}</strong></p>
    {deadline_text}
    <p>Please log in to TimeGuard to view the full details and start working on this task.</p>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = to_email
    
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Task assignment notification sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send task assignment email to {to_email}: {e}")
        raise

def send_deadline_missed_alert(admin_email, task_title, user_name, deadline):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    
    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    
    subject = f"TimeGuard - Deadline Missed: {task_title}"
    
    html_content = f"""
    <h2>Task Deadline Missed</h2>
    <p><strong>{user_name}</strong> has missed the deadline for task: <strong>{task_title}</strong></p>
    <p><strong>Deadline was:</strong> {format_ist_datetime(deadline)}</p>
    <p>Please follow up with the user or reassign the task as needed.</p>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = admin_email
    
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, admin_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Deadline missed alert sent to {admin_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send deadline alert to {admin_email}: {e}")
        raise
def send_task_completion_alert(admin_email, task_title, user_name, completion_time, actual_time=None):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    
    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    
    subject = f"TimeGuard - Task Completed: {task_title}"
    time_info = f"<p><strong>Time Spent:</strong> {actual_time:.2f} hours</p>" if actual_time else ""
    
    html_content = f"""
    <h2>Task Completed</h2>
    <p><strong>{user_name}</strong> has completed the task: <strong>{task_title}</strong></p>
    <p><strong>Completed At:</strong> {format_ist_datetime(completion_time)}</p>
    {time_info}
    <p>Log in to TimeGuard to view the full details.</p>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = admin_email
    
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, admin_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Task completion alert sent to {admin_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send task completion alert to {admin_email}: {e}")
        raise
def send_registration_otp(to_email, otp_code):
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    sender_name = current_app.config.get('SMTP_SENDER_NAME', 'TimeGuard Admin')
    
    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in config.")
    
    subject = "TimeGuard - Email Verification OTP"
    html_content = f"""
    <h2>Welcome to TimeGuard!</h2>
    <p>Your email verification OTP is: <strong>{otp_code}</strong></p>
    <p>This OTP will expire in 10 minutes.</p>
    <p>Please enter this code to complete your registration.</p>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{smtp_user}>"
    msg['To'] = to_email
    
    part_html = MIMEText(html_content, 'html')
    msg.attach(part_html)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Registration OTP sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send registration OTP to {to_email}: {e}")
        raise