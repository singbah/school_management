from datetime import datetime, timedelta
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["argon2"])

SECRET_KEY = os.getenv("SECRET_KEY", 'super_key')
ALGORITHM = os.getenv("ALGORITHM")

def set_password(password:str):
    if password and len(password) > 3:
        hash_password = pwd_context.hash(password)
        return hash_password
    else:
        return "Password must be greater or equal 4"

def verify_password(plain:str, hash_pwd):
    if not all([plain, hash_pwd]):
        return "error!"
    return pwd_context.verify(plain, hash_pwd)
