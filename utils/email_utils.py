def generate_task_history_text(user, tasks):
    lines = [f"Task History for {user.username}",
             "Title,Status,Priority,Category,Created,Started,Completed,Actual Time (h)"]
    for t in tasks:
        line = f'"{t.title}","{t.status}","{t.priority}","{t.category or ''}","{t.created_at.strftime('%Y-%m-%d %H:%M')}","{t.started_at.strftime('%Y-%m-%d %H:%M') if t.started_at else ''}","{t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else ''}","{t.actual_time or '-'}"'
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

def generate_weekly_summary(user, tasks):
    completed_tasks = [t for t in tasks if t.status == 'completed' and t.completed_at and t.completed_at >= datetime.utcnow() - timedelta(days=7)]
    total_time = sum(t.actual_time or 0 for t in completed_tasks)
    task_count = len(completed_tasks)
    # Performance trend: compare to previous week
    prev_week_tasks = [t for t in tasks if t.status == 'completed' and t.completed_at and datetime.utcnow() - timedelta(days=14) <= t.completed_at < datetime.utcnow() - timedelta(days=7)]
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
            <td>{t.completed_at.strftime('%Y-%m-%d %H:%M')}</td>
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
            <td>{t.created_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td>{t.started_at.strftime('%Y-%m-%d %H:%M') if t.started_at else ''}</td>
            <td>{t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else ''}</td>
            <td>{t.actual_time or '-'}</td>
        </tr>
        """
    html += "</table>"
    return html
