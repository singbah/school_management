from fastapi import APIRouter, HTTPException, status, Request, Response, Form, UploadFile, File, Query
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.database import db
from src.schemas import CreateStudent, StudentLogin
from src.routes.auths import set_password, verify_password
from src.routes.config.security import create_token, verify_token, validate_phone
import uuid

load_dotenv()
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

user_auths_bp = APIRouter(prefix="/api/user/auths")

@user_auths_bp.post("/register")
async def student_register(user:CreateStudent, request:Request, response:Response):
    try:
        now = datetime.now()
        if user.phone:
            validate_phone(user.phone)
        existing_user = await db.students.find_one({"$or":[{"email":user.email}, {"phone":user.phone}]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists"
            )
        hashed_password = set_password(user.password)
        user_dict = user.dict()

        user_dict["password"] = hashed_password
        user_dict["created_at"] = now
        user_dict["updated_at"] = now
        user_dict["student_id"] = str(uuid.uuid4().int)[0:4]
        user_dict["failed_attempts"] = 0
        user_dict["lockout_time"] = None
        await db.students.insert_one(user_dict)

        return {"message":"User registered successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_auths_bp.post("/login")
async def student_login(login_data:StudentLogin, request:Request, response:Response):
    print(login_data)
    try:
        now = datetime.now()
        ip = request.client.host
        user = await db.students.find_one({"student_id": login_data.student_id})
        print(user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.get("lockout_time") and now < user["lockout_time"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked. Please try again later."
            )
        if not verify_password(login_data.password, user["password"]):
            await db.students.update_one({"student_id": login_data.student_id}, {"$inc": {"failed_attempts": 1}})
            if user["failed_attempts"] + 1 >= MAX_ATTEMPTS:
                lockout_time = now + LOCKOUT_DURATION
                await db.students.update_one({"student_id": login_data.student_id}, {"$set": {"lockout_time": lockout_time}})
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked due to too many failed login attempts. Please try again later."
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        await db.students.update_one({"student_id": login_data.student_id}, {"$set": {"failed_attempts": 0, "lockout_time": None, "last_login": now, "last_ip": ip}})

        token_data = {
            "student_id": user["student_id"],
            "email": user["email"],
            'role': 'student'
        }

        access_token = create_token(token_data)
        refresh_token = create_token(token_data, expires_delta=60*60*24*7)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
        )
    
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
        )

        user['_id'] = str(user["_id"])
        return {'detail':user}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )