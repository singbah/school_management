from datetime import datetime, timedelta
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import FileSystemLoader, Environment, select_autoescape

from src.database import db

load_dotenv()

pwd_context = CryptContext(schemes=["argon2"])

SECRET_KEY = os.getenv("SECRET_KEY", 'super_key')
ALGORITHM = os.getenv("ALGORITHM", 'HS256')

MAIL_USERNAME = str(os.getenv("MAIL_USERNAME"))
MAIL_PASSWORD = str(os.getenv("MAIL_PASSWORD"))
MAIL_FROM = str(os.getenv("MAIL_FROM"))
MAIL_SERVER = str(os.getenv("MAIL_SERVER"))
MAIL_PORT = int(os.getenv("MAIL_PORT")) if os.getenv("MAIL_PORT") else 587
MAIL_USE_TLS = bool(os.getenv("MAIL_USE_TLS")) if os.getenv("MAIL_USE_TLS") else True
MAIL_USE_SSL = bool(os.getenv("MAIL_USE_SSL")) if os.getenv("MAIL_USE_SSL") else False

env = Environment(
    loader=FileSystemLoader(os.path.join(os.getcwd(), "templates", 'emails')),
    autoescape=select_autoescape(["html", "xml"])
)

mail_config = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_SSL_TLS=MAIL_USE_SSL,
    MAIL_STARTTLS=MAIL_USE_TLS
)


def set_password(password:str):
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)

def verify_password(plain:str, hash_pwd):
    if not all([plain, hash_pwd]):
        raise ValueError("Both plain and hashed passwords are required")
    return pwd_context.verify(plain, hash_pwd)

async def send_email(subject:str, recipient:str, msg:str, username:str):
    if not all([subject, recipient, msg, username]):
        raise ValueError("Subject, recipient, message, and username are required")
    
    template = env.get_template("email.html")
    html_content = template.render(username=username, message=msg)

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        html=html_content
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)
