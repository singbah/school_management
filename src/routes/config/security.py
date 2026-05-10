from datetime import datetime, timedelta

from dotenv import load_dotenv
import os
from fastapi import HTTPException, status
from jose import jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", 'super_key')
ALGORITHM = os.getenv("ALGORITHM", 'HS256')

def create_token(data:dict, expires_delta=60*2):
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(minutes=expires_delta)
            to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def verify_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

def validate_phone(phone:str):
    ext_ = ['055', '088', '077', '076']
    if not phone.startswith(tuple(ext_)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    if len(phone) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be 10 digits long"
        )