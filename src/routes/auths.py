from datetime import datetime, timedelta
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os
import hashlib
import secrets

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", 'super_key')
ALGORITHM = os.getenv("ALGORITHM")
salt = secrets.token_bytes(16)

def set_password(password:str):
    try:
        if len(password) < 4:
            raise HTTPException(
                status_code=status.HTTP_411_LENGTH_REQUIRED,
                detail="password must be longer the 3"
            )
        hash_object = hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"), salt, 10000)
        hash_password = salt + hash_object
        return hash_password
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def verify_password(plain:str, hash_pwd):
    if not plain or hash_pwd:
        return False
    try:
        salt = hash_pwd[:16]
        store_password = hash_pwd[16:]
        print(plain)
        
        new_hash = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 10000)

        if new_hash == store_password:
            return True
        
        return False
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

