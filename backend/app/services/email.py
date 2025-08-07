import logging
from fastapi import BackgroundTasks
from typing import Optional, List, Dict, Any
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from pathlib import Path
from jinja2 import Environment, select_autoescape, PackageLoader
import os

# Set up logger
logger = logging.getLogger(__name__)

# Define template folder path
template_folder = Path(__file__).parent.parent / "templates"

# Create template folder if it doesn't exist
if not template_folder.exists():
    try:
        template_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created template directory at {template_folder}")
    except Exception as e:
        logger.error(f"Failed to create template directory: {e}")

# Configure FastMail with updated parameter names for FastAPI Mail v1.4+
conf_params = {
    "MAIL_USERNAME": settings.MAIL_USERNAME,
    "MAIL_PASSWORD": settings.MAIL_PASSWORD,
    "MAIL_FROM": settings.MAIL_FROM,
    "MAIL_PORT": settings.MAIL_PORT,
    "MAIL_SERVER": settings.MAIL_SERVER,
    "MAIL_FROM_NAME": "Sonicus Therapy",
    "MAIL_STARTTLS": settings.MAIL_TLS,
    "MAIL_SSL_TLS": settings.MAIL_SSL,
    "USE_CREDENTIALS": True,
    "VALIDATE_CERTS": True,
}

# Only add template folder if it exists
if template_folder.exists() and template_folder.is_dir():
    conf_params["TEMPLATE_FOLDER"] = template_folder

try:
    conf = ConnectionConfig(**conf_params)
except Exception as e:
    logger.error(f"Failed to configure email: {str(e)}")
    conf = None

# Initialize Jinja2 environment for email templates
try:
    if template_folder.exists() and template_folder.is_dir():
        template_env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            loader=PackageLoader('app', 'templates'),
        )
    else:
        template_env = None
        logger.warning("Templates directory not found, template rendering disabled")
except Exception as e:
    logger.warning(f"Failed to initialize template environment: {str(e)}")
    template_env = None

def send_invoice_email(background_tasks: BackgroundTasks, user_email: str, invoice_id: int):
    """Add email sending task to background tasks."""
    background_tasks.add_task(_send_email_task, 
                             user_email, 
                             "Your Invoice",
                             f"Your invoice #{invoice_id} is ready to view.",
                             {"invoice_id": invoice_id})

async def _send_email_task(
    user_email: str, 
    subject: str,
    body: str,
    template_data: Optional[Dict[str, Any]] = None
) -> Optional[bool]:
    """Send an email with error handling."""
    try:
        if not all([settings.MAIL_USERNAME, settings.MAIL_PASSWORD, settings.MAIL_SERVER]):
            logger.warning(f"Email configuration incomplete. Simulating sending email to {user_email}")
            print(f"SIMULATED EMAIL TO: {user_email}\nSUBJECT: {subject}\nBODY: {body}")
            return True
        
        if conf is None:
            logger.error("Email configuration failed, cannot send email")
            return False
            
        # Create message
        message = MessageSchema(
            subject=subject,
            recipients=[user_email],
            body=body,
            subtype=MessageType.html
        )
        
        # Send email
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Email sent to {user_email}: {subject}")
        return True
        
    except Exception as e:
        # Log the error but don't crash the application
        logger.error(f"Failed to send email to {user_email}: {str(e)}")
        return False

def send_password_reset_email(background_tasks: BackgroundTasks, user_email: str, reset_token: str):
    """Add password reset email task to background tasks."""
    reset_url = f"{settings.API_V1_STR}/auth/reset-password?token={reset_token}"
    subject = "Password Reset Request"
    
    # Create email body
    body = f"""
    <html>
        <body>
            <h1>Password Reset Request</h1>
            <p>Hello,</p>
            <p>We received a request to reset your password. Use the token below to reset your password:</p>
            <p><strong>{reset_token}</strong></p>
            <p>This token will expire in 24 hours.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Best regards,<br>Sonicus Team</p>
        </body>
    </html>
    """
    
    background_tasks.add_task(_send_email_task, user_email, subject, body, {"reset_token": reset_token, "reset_url": reset_url})

def send_welcome_email(background_tasks: BackgroundTasks, user_email: str):
    """Send a welcome email to newly registered users."""
    subject = "Welcome to Sonicus Therapy"
    body = """
    <html>
        <body>
            <h1>Welcome to Sonicus Therapy</h1>
            <p>Hello,</p>
            <p>Thank you for registering with Sonicus Therapy. We're excited to have you on board!</p>
            <p>Start exploring our collection of therapeutic sounds to enhance your wellbeing.</p>
            <p>Best regards,<br>The Sonicus Team</p>
        </body>
    </html>
    """
    
    background_tasks.add_task(_send_email_task, user_email, subject, body)
