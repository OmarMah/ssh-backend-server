from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import Dict, Any
import os
import json
import tempfile
import aiofiles

class SshKeyData(BaseModel):
    username: str
    email: str
    jobDescription: str
    sshKey: str

app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "https://ssh-key-form-builder.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Email Configuration ---
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-email-password")
MAIL_FROM = os.getenv("MAIL_FROM", "your-email@example.com")
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
    TEMPLATE_FOLDER=None
)

RECIPIENT_EMAIL = "salmamohammedhamed2@gmail.com"

async def send_email_background(subject: str, recipient: EmailStr, body: Dict[str, Any], attachment_data: str):
    message_body_html = f"""
    <p>New SSH Key submission:</p>
    <p><strong>Username:</strong> {body.get("username")}</p>
    <p><strong>Email:</strong> {body.get("email")}</p>
    <p><strong>Job Description:</strong> {body.get("jobDescription")}</p>
    <p>Full details are in the attached JSON file.</p>
    """

    temp_file_descriptor, temp_file_path = tempfile.mkstemp(suffix=".json", text=True)
    os.close(temp_file_descriptor)

    async with aiofiles.open(temp_file_path, mode='w', encoding='utf-8') as tmp_file:
        await tmp_file.write(attachment_data)

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=message_body_html,
        subtype=MessageType.html,
        attachments=[temp_file_path]
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

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
