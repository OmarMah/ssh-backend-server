from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import Dict, Any
import os
import json

class SshKeyData(BaseModel):
    username: str
    email: EmailStr
    sshKey: str

app = FastAPI()

# --- Email Configuration ---

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-email-password")
MAIL_FROM = EmailStr(os.getenv("MAIL_FROM", "your-email@example.com"))
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.example.com")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=None # No templates needed for this simple case
)

RECIPIENT_EMAIL = "reromahmoud1995@gmail.com"

async def send_email_background(subject: str, recipient: EmailStr, body: Dict[str, Any], attachment_data: str):
    message_body_html = f"""
    <p>New SSH Key submission:</p>
    <p><strong>Username:</strong> {body.get("username")}</p>
    <p><strong>Email:</strong> {body.get("email")}</p>
    <p>Full details are in the attached JSON file.</p>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=message_body_html,
        subtype=MessageType.html,
        attachments=[{
            "file": attachment_data.encode('utf-8'),
            "filename": "ssh_key_data.json",
            "mime_type": "application/json"
        }]
    )

    fm = FastMail(conf)
    await fm.send_message(message)


@app.post("/api/send-ssh-key/")
async def send_ssh_key_email(data: SshKeyData, background_tasks: BackgroundTasks):
    email_subject = f"SSH Key Submission from {data.username}"
    
    form_data_dict = data.model_dump()
    json_attachment_content = json.dumps(form_data_dict, indent=2)

    background_tasks.add_task(
        send_email_background, 
        email_subject, 
        RECIPIENT_EMAIL, 
        form_data_dict, 
        json_attachment_content
    )
    
    return {"message": "SSH key data is being processed and will be sent via email."}

